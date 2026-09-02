#!/usr/bin/env bash
set -Eeuo pipefail

readonly REPO_URL="https://github.com/weby-homelab/Must-Inverter-Dashboard.git"
readonly INSTALL_DIR="/opt/must-inverter-dashboard"
readonly SERVICE_NAME="must-inverter-dashboard.service"
readonly SERVICE_USER="mustdash"
readonly VERSION="${1:-v0.1.1}"

fail() {
    printf 'ERROR: %s\n' "$1" >&2
    exit 1
}

if [[ "${EUID}" -ne 0 ]]; then
    fail "run this installer as root, for example: curl ... | sudo bash"
fi

if [[ "$(uname -s)" != "Linux" ]]; then
    fail "this installer supports Linux only"
fi

command -v apt-get >/dev/null 2>&1 || fail "this one-command installer supports Debian/Ubuntu (apt-get)"

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y ca-certificates curl git python3 python3-venv python3-pip acl

if [[ -e "${INSTALL_DIR}" && ! -d "${INSTALL_DIR}/.git" ]]; then
    fail "${INSTALL_DIR} exists and is not a Git checkout"
fi

if [[ -d "${INSTALL_DIR}/.git" ]]; then
    if [[ -n "$(git -C "${INSTALL_DIR}" status --porcelain)" ]]; then
        fail "${INSTALL_DIR} has local changes; refusing to overwrite them"
    fi
    git -C "${INSTALL_DIR}" fetch --tags origin
    git -C "${INSTALL_DIR}" checkout --detach "${VERSION}"
else
    git clone --branch "${VERSION}" --depth 1 "${REPO_URL}" "${INSTALL_DIR}"
fi

if ! id -u "${SERVICE_USER}" >/dev/null 2>&1; then
    useradd --system --user-group --home-dir "${INSTALL_DIR}" --shell /usr/sbin/nologin "${SERVICE_USER}"
fi
usermod --append --groups dialout "${SERVICE_USER}"

python3 -m venv "${INSTALL_DIR}/.venv"
"${INSTALL_DIR}/.venv/bin/python" -m pip install --disable-pip-version-check --no-cache-dir -r "${INSTALL_DIR}/requirements.txt"

env_created=0
if [[ ! -e "${INSTALL_DIR}/.env" ]]; then
    install -o root -g "${SERVICE_USER}" -m 0640 "${INSTALL_DIR}/.env.example" "${INSTALL_DIR}/.env"
    env_created=1
fi

serial_device=""
for candidate in /dev/serial/by-id/*; do
    if [[ -e "${candidate}" ]]; then
        serial_device="${candidate}"
        break
    fi
done
if [[ "${env_created}" -eq 1 && -n "${serial_device}" ]] && grep -q '^MUST_SERIAL_PORT=' "${INSTALL_DIR}/.env"; then
    escaped_serial="${serial_device//|/\\|}"
    sed -i "s|^MUST_SERIAL_PORT=.*|MUST_SERIAL_PORT=${escaped_serial}|" "${INSTALL_DIR}/.env"
fi

install -d -o "${SERVICE_USER}" -g "${SERVICE_USER}" -m 0750 "${INSTALL_DIR}/data"
chown -R root:root "${INSTALL_DIR}"
chown "${SERVICE_USER}:${SERVICE_USER}" "${INSTALL_DIR}/.env" "${INSTALL_DIR}/data"
chmod 0640 "${INSTALL_DIR}/.env"
chmod 0750 "${INSTALL_DIR}/data"

install -o root -g root -m 0644 "${INSTALL_DIR}/deploy/${SERVICE_NAME}" "/etc/systemd/system/${SERVICE_NAME}"
systemctl daemon-reload
systemctl enable --now "${SERVICE_NAME}"

"${INSTALL_DIR}/.venv/bin/python" -m unittest discover -s "${INSTALL_DIR}/tests" -v

for _ in {1..30}; do
    if curl --fail --silent --show-error --max-time 3 http://127.0.0.1:8090/healthz >/dev/null; then
        printf 'MUST Power Desk %s is installed and ready at http://127.0.0.1:8090\n' "${VERSION}"
        exit 0
    fi
    sleep 1
done

systemctl --no-pager --full status "${SERVICE_NAME}" || true
fail "service did not become ready; inspect: journalctl -u ${SERVICE_NAME} -n 100 --no-pager"
