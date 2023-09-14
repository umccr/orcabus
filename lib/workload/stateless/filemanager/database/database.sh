function usage() {
  usage="$(basename "$0") [-h] [-u <USER>] [-c init|migrate|reset] -- administer the filemanager database.

  commands:
    init  initialize the database
    migrate  migrate the database using files in the migrations directory
    reset  drop and recreate the database

  options:
      -h  show this help text
      -u  set the user for the database [default: POSTGRES_USER environment variable or not set]
      -c  the command for this script to run [default: not set, required]"

  echo "$usage"
}

function run_command() {
  if [[ "$command" == "init" ]]; then
    /bin/bash init_database.sh "${args[@]}"
  elif [[ "$command" == "migrate" ]]; then
    /bin/bash migrate.sh "${args[@]}"
  elif [[ "$command" == "reset" ]]; then
    /bin/bash reset_database.sh "${args[@]}"
  else
    printf "unknown command: -%s\n" "$command" >&2
    usage >&2
    exit 1
  fi
}

function set_args() {
    if [[ -n "${POSTGRES_USER}" ]]; then
      echo "Using ${POSTGRES_USER} as the postgres user"
      args+=( "--username" )
      args+=( "POSTGRES_USER" )
    else
      echo "No user supplied, using default"
    fi
}

args=()
command=""
while getopts ':hu:c:' option; do
  case "$option" in
    h)
      usage
      exit
      ;;
    u)
      args+=( "--username" )
      args+=( "$OPTARG" )
      ;;
    c)
      command="$OPTARG"
      ;;
    :)
      printf "missing argument for -%s\n" "$OPTARG" >&2
      usage >&2
      exit 1
      ;;
    \?)
      printf "invalid option: -%s\n" "$OPTARG" >&2
      usage >&2
      exit 1
      ;;
  esac
done
shift $((OPTIND - 1))

if [[ ${#args[@]} -eq 0 ]]; then
  set_args
fi

run_command