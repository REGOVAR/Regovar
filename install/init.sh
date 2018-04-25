#!/bin/bash


# =======================================================================================
# Script tools
# =======================================================================================
NC="\033[0m"
BLACK="\033[0;90m"
RED="\033[0;91m"
GREEN="\033[0;92m"
YELLOW="\033[0;93m"
BLUE="\033[0;94m"
PURPLE="\033[0;95m"
CYAN="\033[0;96m"
WHITE="\033[0;97m"



# =======================================================================================
# Check prerequisites
# =======================================================================================
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}Error: This script must be run as root${NC}" 1>&2
   echo "We need root priviledges for:"
   echo " - creating folders in /var (by default)"
   echo " - using docker service"
   echo " - setting up nginx for regovar"
   echo "Note that the regovar service don't need root priviledges as it is virtualized in docker"
   exit 1
fi



# =======================================================================================
# Default config value
# =======================================================================================
debug="n"
root_folder="/var/regovar2"
random_key32=`cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1`
omim_key="piout"
public_host="localhost2"
db_user="regovar2"
db_pwd="regovar2"
db_name="regovar2"
regovar_pg_port=20051
regovar_app_port=20050


# =======================================================================================
# Ask user to set main config settings
# =======================================================================================
echo -e "${CYAN}\n __   ___  __   __             __  \n|__) |__  / _\` /  \ \  /  /\  |__) \n|  \ |___ \__) \__/  \/  /~~\ |  \ \n${NC}"
echo -e "This script will help you to install and configure regovar server.\nYou will have to answer to 7 questions.\n"
echo -n "1) Root folder where Regovar data will be stored (default: $root_folder): "
read answer
if [ -n "$answer" ]; then
    root_folder=$answer
fi

echo -n "2) Enable debug log [y|n] (default: $debug): "
read answer
if [ -n "$answer" ]; then
    debug=$answer
fi
if [ "n" == "$debug" ]; then
    debug=False
else
    debug=True
fi

echo -n "3) Private 32 bits key used to encrypts coockies and security token (HTTPS) (default: random generation): "
read answer
if [ -n "$answer" ]; then
    random_key32=$answer
fi

echo -n "4) OMIM API key: "
read answer
if [ -n "$answer" ]; then
    omim_key=$answer
fi

echo -n "5) Public hostname (default: $public_host):"
read answer
if [ -n "$answer" ]; then
    public_host=$answer
fi

echo "6) Database parameters: "
echo -n "   - USER: (default: $db_user): "
read answer
if [ -n "$answer" ]; then
    db_user=$answer
fi

echo -n "   - PASSWORD: (default: $db_pwd): "
read answer
if [ -n "$answer" ]; then
    db_pwd=$answer
fi

echo -n "   - DB NAME: (default: $db_name): "
read answer
if [ -n "$answer" ]; then
    db_name=$answer
fi

echo "7) Docker containers exposed ports:"
echo -n "   - database port: (default: $regovar_pg_port): "
read answer
if [ -n "$answer" ]; then
    regovar_pg_port=$answer
fi

echo -n "   - application port: (default: $regovar_app_port): "
read answer
if [ -n "$answer" ]; then
    regovar_app_port=$answer
fi



# =======================================================================================
# Resume user settings
# =======================================================================================
echo -e "\nThanks!\nWe will generate for you the configs files with provided informations:"
echo -e " - ${WHITE}HOST_ROOT:${NC}\t\t$root_folder"
echo -e " - ${WHITE}DEBUG:${NC}\t\t$debug"
echo -e " - ${WHITE}PRIVATE_KEY32:${NC}\t$random_key32"
echo -e " - ${WHITE}OMIM_API_KEY:${NC}\t$omim_key"
echo -e " - ${WHITE}HOST_P:${NC}\t\t$public_host"
echo -e " - ${WHITE}DATABASE_USER:${NC}\t$db_user"
echo -e " - ${WHITE}DATABASE_PWD:${NC}\t$db_pwd"
echo -e " - ${WHITE}DATABASE_NAME:${NC}\t$db_name"
echo -e " - ${WHITE}DB_PORT:${NC}\t\t$regovar_pg_port"
echo -e " - ${WHITE}APP_PORT:${NC}\t\t$regovar_app_port"




echo -e "\nSetting up Regovar:\n======================================================================================="
# =======================================================================================
# Preparing files repository on HOST
# =======================================================================================
if test "$(ls -A "$root_folder")"; then
    echo -e "  ${YELLOW}Warning:${NC} The directory $root_folder already exists."
    echo -e -n "           Move all its content to $root_folder-bak and continue (yes) ? Or cancel installation (no) [y|n]: "
    read answer
    if [ "y" == "$answer" ]; then
        mv -f $root_folder $root_folder-bak
    else
        echo -e "  ${RED}Error:${NC} Installation canceled"
        exit 2
    fi
fi
mkdir -p $root_folder/{app,config,cache,downloads,files,pipelines,jobs,pgdata,databases/hg19,databases/hg38}
echo -e "  ${GREEN}Done:${NC} Regovar folders created on HOST: $root_folder"



# =======================================================================================
# Generating: regovar_app Dockerfile
# =======================================================================================
echo -e -n "  ${YELLOW}In progress${NC}: Generating Dockerfile for regovar_app docker image"
cp config/dockerfile.default $root_folder/config/Dockerfile
# Nothing to do ...
echo -e "\r  ${GREEN}Done${NC}: Generating Dockerfile for regovar_app docker image"



# =======================================================================================
# Generating: docker-compose
# =======================================================================================
echo -e -n "  ${YELLOW}In progress${NC}: Generating docker-compose file"
cp config/docker-compose.default $root_folder/config/regovar.yml
# (      - /var/regovar)/pgdata...    => (      - $root_folder)/pgdata...
# (      - /var/regovar)/databases... => (      - $root_folder)/databases...
# (      - /var/regovar):...          => (      - $root_folder):...
sed -i 's/^\(\s*\/var\/regovar\)\(\/pgdata.*\)/$(root_folder)\2/' $root_folder/config/regovar.yml
sed -i 's/^\(\s*\/var\/regovar\)\(\/databases.*\)/$(root_folder)\2/' $root_folder/config/regovar.yml
sed -i 's/^\(\s*\/var\/regovar\)\(\:.*\)/$(root_folder)\2/' $root_folder/config/regovar.yml
echo -e "\r  ${GREEN}Done${NC}: Generating docker-compose file"





# =======================================================================================
# Generating: regovar config.py
# =======================================================================================
echo -e -n "  ${YELLOW}In progress${NC}: Generating regovar app python config file"
cp config/config.default $root_folder/config/config.py
sed -i 's/^\(\s*DEBUG\s*=\s*\)(.*\)/\1$(debug)/' $root_folder/config/config.py
sed -i 's/^\(\s*HOST_P\s*=\s*"\)\([^"]\+\)\(".*\)/\1$(public_host)\3/' $root_folder/config/config.py
sed -i 's/^\(\s*PRIVATE_KEY32\s*=\s*"\)\([^"]\+\)\(".*\)/\1$(random_key32)\3/' $root_folder/config/config.py
sed -i 's/^\(\s*OMIM_API_KEY\s*=\s*"\)\([^"]\+\)\(".*\)/\1$(omim_key)\3/' $root_folder/config/config.py
sed -i 's/^\(\s*DATABASE_USER\s*=\s*"\)\([^"]\+\)\(".*\)/\1$(db_user)\3/' $root_folder/config/config.py
sed -i 's/^\(\s*DATABASE_PWD\s*=\s*"\)\([^"]\+\)\(".*\)/\1$(db_pwd)\3/' $root_folder/config/config.py
sed -i 's/^\(\s*DATABASE_NAME\s*=\s*"\)\([^"]\+\)\(".*\)/\1$(db_name)\3/' $root_folder/config/config.py
echo -e "\r  ${GREEN}Done${NC}: Generating regovar app python config file"








# =======================================================================================
# Generating: nginx sites-availables file
# =======================================================================================
echo -e -n "  ${YELLOW}In progress${NC}: Generating nginx config file"
cp config/nginx.default $root_folder/config/regovar
echo -e -n "  ${GREEN}Done${NC}: Generating nginx config file"

# regovar_pg_port=10051
# regovar_app_port=10050




# =======================================================================================
# Build regovar container
# =======================================================================================




# =======================================================================================
# Install regovar application and database
# =======================================================================================




# =======================================================================================
# Test
# =======================================================================================


echo -e "\nFinnish ! "
chown olivier:olivier -R $root_folder


                                   