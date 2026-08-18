#!/usr/bin/env bash
set -euo pipefail

repository_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
config_file=${AQENO_RH1_CONFIG:-${repository_root}/deploy/rh1.local}
if [[ -f ${config_file} ]]; then
  # This is developer-owned configuration, never device/user state.
  # shellcheck disable=SC1090
  source "${config_file}"
fi

host=${AQENO_RH1_HOST:-aqeno.local}
user=${AQENO_RH1_USER:-aqeno-dev}
port=${AQENO_RH1_SSH_PORT:-22}
identity=${AQENO_RH1_IDENTITY:-}

if [[ ! ${host} =~ ^[A-Za-z0-9.-]+$ ]]; then
  echo "Invalid AQENO_RH1_HOST: ${host}" >&2
  exit 2
fi
if [[ ! ${user} =~ ^[a-z_][a-z0-9_-]*$ ]]; then
  echo "Invalid AQENO_RH1_USER: ${user}" >&2
  exit 2
fi
if [[ ! ${port} =~ ^[0-9]+$ ]]; then
  echo "Invalid AQENO_RH1_SSH_PORT: ${port}" >&2
  exit 2
fi

ssh_options=(-p "${port}" -o BatchMode=yes)
rsync_transport="ssh -p ${port} -o BatchMode=yes"
if [[ -n ${identity} ]]; then
  [[ ${identity} != *[[:space:]]* && -f ${identity} ]] \
    || { echo "AQENO_RH1_IDENTITY must be an existing path without whitespace" >&2; exit 2; }
  ssh_options+=(-i "${identity}")
  rsync_transport+=" -i ${identity}"
fi
target=${user}@${host}
helper=(sudo -n /usr/local/libexec/aqeno-devctl)

remote() {
  ssh "${ssh_options[@]}" "${target}" "$@"
}

require_command() {
  if ! command -v "$1" >/dev/null; then
    echo "Required local command is missing: $1" >&2
    exit 2
  fi
}

build_admin() {
  require_command npm
  (cd "${repository_root}/admin" && npm run check && npm run build)
}

fast_deploy() {
  require_command rsync
  build_admin
  build_id="dev-$(git -C "${repository_root}" rev-parse --short=12 HEAD)"
  remote_root="/var/tmp/aqeno-upload/${user}/${build_id}"
  remote "mkdir -p '${remote_root}/source' '${remote_root}/admin'"
  rsync -az --delete -e "${rsync_transport}" \
    --exclude '__pycache__/' --exclude '*.pyc' \
    "${repository_root}/src" "${repository_root}/pyproject.toml" \
    "${target}:${remote_root}/source/"
  rsync -az --delete -e "${rsync_transport}" \
    "${repository_root}/admin/build/" "${target}:${remote_root}/admin/"
  remote "${helper[*]} activate-dev '${remote_root}'"
}

release_deploy() {
  require_command rsync
  build_admin
  staging=$(mktemp -d)
  trap 'rm -rf -- "${staging}"' EXIT
  revision=$(git -C "${repository_root}" rev-parse --short=12 HEAD)
  version=$("${repository_root}/.venv/bin/python" -c \
    'import sys, tomllib; print(tomllib.load(open(sys.argv[1], "rb"))["project"]["version"])' \
    "${repository_root}/pyproject.toml")
  release_id="${version}-${revision}-$(date -u +%Y%m%dT%H%M%SZ)"
  mkdir -p "${staging}/admin" "${staging}/package"
  "${repository_root}/.venv/bin/pip" wheel --wheel-dir "${staging}/package" \
    "${repository_root}[rh1]"
  cp -a "${repository_root}/admin/build/." "${staging}/admin/"
  printf '{"release_id":"%s","revision":"%s"}\n' "${release_id}" "${revision}" \
    >"${staging}/release.json"
  remote_root="/var/tmp/aqeno-upload/${user}/${release_id}"
  remote "mkdir -p '${remote_root}'"
  rsync -az --delete -e "${rsync_transport}" "${staging}/" "${target}:${remote_root}/"
  remote "${helper[*]} activate-release '${remote_root}' '${release_id}'"
}

case ${1:-} in
  dev) fast_deploy ;;
  release) release_deploy ;;
  ssh) exec ssh "${ssh_options[@]}" "${target}" ;;
  status) remote "${helper[*]} status" ;;
  logs) remote "${helper[*]} logs-follow" ;;
  logs-once) remote "${helper[*]} logs" ;;
  restart) remote "${helper[*]} restart" ;;
  health) remote "${helper[*]} health" ;;
  diagnostics) remote "${helper[*]} diagnostics" ;;
  *)
    echo "Usage: $0 {dev|release|ssh|status|logs|logs-once|restart|health|diagnostics}" >&2
    exit 2
    ;;
esac
