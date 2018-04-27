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
# if [[ $EUID -ne 0 ]]; then
#    echo -e "${RED}Error: This script must be run as root${NC}" 1>&2
#    echo "We need root priviledges for:"
#    echo " - creating folders in /var (by default)"
#    echo " - using docker service"
#    echo " - setting up nginx for regovar"
#    echo "Note that the regovar service don't need root priviledges as it is virtualized in docker"
#    exit 1
# fi

# TODO: better way to retrieve parent folder of the script ?
git_path=$PWD/..



# =======================================================================================
# Default config value
# =======================================================================================
debug="n"
root_folder="/var/regovar"
random_key32=`cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1`
omim_key=""
public_host="dev.regovar.org"
db_user="regovar"
db_pwd="regovar"
db_name="regovar"
regovar_pg_port=5432
regovar_app_port=8500


# =======================================================================================
# Ask user to set main config settings
# =======================================================================================
echo -e "${CYAN}\n __   ___  __   __             __  \n|__) |__  / _\` /  \ \  /  /\  |__) \n|  \ |___ \__) \__/  \/  /~~\ |  \ \n${NC}"
echo -e "This script will help you to install and configure regovar server.\nYou will have to answer to 7 questions.\n"
# echo -n "1) Root folder where Regovar data will be stored (default: $root_folder): "
# read answer
# if [ -n "$answer" ]; then
#     root_folder=$answer
# fi
# 
# echo -n "2) Enable debug log [y|n] (default: $debug): "
# read answer
# if [ -n "$answer" ]; then
#     debug=$answer
# fi
if [ "n" == "$debug" ]; then
    debug=False
else
    debug=True
fi
# 
# echo -n "3) Private 32 bits key used to encrypts coockies and security token (HTTPS) (default: random generation): "
# read answer
# if [ -n "$answer" ]; then
#     random_key32=$answer
# fi
# 
# echo -n "4) OMIM API key: "
# read answer
# if [ -n "$answer" ]; then
#     omim_key=$answer
# fi
# 
# echo -n "5) Public hostname (default: $public_host): "
# read answer
# if [ -n "$answer" ]; then
#     public_host=$answer
# fi
# 
# echo "6) Database parameters: "
# echo -n "   - USER: (default: $db_user): "
# read answer
# if [ -n "$answer" ]; then
#     db_user=$answer
# fi
# 
# echo -n "   - PASSWORD: (default: $db_pwd): "
# read answer
# if [ -n "$answer" ]; then
#     db_pwd=$answer
# fi
# 
# echo -n "   - DB NAME: (default: $db_name): "
# read answer
# if [ -n "$answer" ]; then
#     db_name=$answer
# fi
# 
# echo "7) Docker containers exposed ports:"
# echo -n "   - database port: (default: $regovar_pg_port): "
# read answer
# if [ -n "$answer" ]; then
#     regovar_pg_port=$answer
# fi
# 
# echo -n "   - application port: (default: $regovar_app_port): "
# read answer
# if [ -n "$answer" ]; then
#     regovar_app_port=$answer
# fi




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




# =======================================================================================
# Preparing files repository on HOST
# =======================================================================================
echo -e "\nGenerating config files:\n======================================================================================="
if test "$(ls -A "$root_folder")"; then
    echo -e "${YELLOW}Warning:${NC} The directory $root_folder already exists."
    echo -e -n "         Erase all content of $root_folder and continue (yes) ? Or cancel installation (no) [y|n]: "
    read answer
    if [ "y" == "$answer" ]; then
        sudo rm -Rf $root_folder
    else
        echo -e "  ${RED}Error:${NC} Installation canceled"
        exit 2
    fi
fi
sudo mkdir -p ${root_folder}/{config,cache,downloads,files,pipelines,jobs,pgdata,databases/hg19,databases/hg38}
sudo chown -R $EUID:$EUID ${root_folder}
echo -e "${GREEN}Done:${NC} Regovar folders created on HOST: $root_folder"

ln -s $git_path/regovar $root_folder/app
cp $git_path/requirements.txt $root_folder/config/requirements.txt
cp $git_path/requirements-dev.txt $root_folder/config/requirements-dev.txt


# =======================================================================================
# Generating: regovar_app Dockerfile
# =======================================================================================
# conver / into \/
sed_root_folder=${root_folder//\//\\/}

echo -e -n "${YELLOW}In progress${NC}: Generating Dockerfile for regovar_app docker image"
cp config/Dockerfile $root_folder/config/Dockerfile
echo -e "\r${GREEN}Done${NC}: Generating Dockerfile for regovar_app docker image"




# =======================================================================================
# Generating: docker-compose
# =======================================================================================
echo -e -n "${YELLOW}In progress${NC}: Generating docker-compose file"
cp config/docker-compose.yml $root_folder/config/regovar.yml
# replace each first occurence of /var/regovar (HOST paths) by provided path
sed -i s/"\/var\/regovar"/"$sed_root_folder"/ $root_folder/config/regovar.yml
sed -i s/"8501"/"$regovar_pg_port"/ $root_folder/config/regovar.yml
sed -i s/"8500"/"$regovar_app_port"/ $root_folder/config/regovar.yml
sed -i s/"localgit"/"${git_path//\//\\/}"/ $root_folder/config/regovar.yml
sed -i s/"^\(\s*POSTGRES_USER\s*=\s*\)\(.*\)"/"\1$db_user"/ $root_folder/config/regovar.yml
sed -i s/"^\(\s*POSTGRES_PASSWORD\s*=\s*\)\(.*\)"/"\1$db_pwd"/ $root_folder/config/regovar.yml
sed -i s/"^\(\s*POSTGRES_DB\s*=\s*\)\(.*\)"/"\1$db_name"/ $root_folder/config/regovar.yml
echo -e "\r${GREEN}Done${NC}: Generating docker-compose file"




# =======================================================================================
# Generating: regovar config.py
# =======================================================================================
echo -e -n "${YELLOW}In progress${NC}: Generating regovar app python config file"
cp config/config.py $root_folder/config/config.py
# conver / into \/ and . into \.
public_host=${public_host//\//\\/}
public_host=${public_host//\./\\.}
sed -i s/"^\(\s*DEBUG\s*=\s*\)\(.*\)"/"\1$debug"/ $root_folder/config/config.py
sed -i s/"^\(\s*HOST_P\s*=\s*\"\)\(.*\)\(\".*\)"/"\1$public_host\3"/ $root_folder/config/config.py
sed -i s/"^\(\s*PRIVATE_KEY32\s*=\s*\"\)\(.*\)\(\".*\)"/"\1$random_key32\3"/ $root_folder/config/config.py
sed -i s/"^\(\s*OMIM_API_KEY\s*=\s*\"\)\(.*\)\(\".*\)"/"\1$omim_key\3"/ $root_folder/config/config.py
sed -i s/"^\(\s*DATABASE_USER\s*=\s*\"\)\(.*\)\(\".*\)"/"\1$db_user\3"/ $root_folder/config/config.py
sed -i s/"^\(\s*DATABASE_PWD\s*=\s*\"\)\(.*\)\(\".*\)"/"\1$db_pwd\3"/ $root_folder/config/config.py
sed -i s/"^\(\s*DATABASE_NAME\s*=\s*\"\)\(.*\)\(\".*\)"/"\1$db_name\3"/ $root_folder/config/config.py
ln -s $root_folder/config/config.py $git_path/regovar/config.py
sudo chown $EUID:$EUID $git_path/regovar/config.py
echo -e "\r${GREEN}Done${NC}: Generating regovar app python config file"




# =======================================================================================
# Generating: nginx sites-availables file
# =======================================================================================
echo -e -n "${YELLOW}In progress${NC}: Generating nginx config file"
cp config/nginx $root_folder/config/nginx
sed -i s/"8500"/"$regovar_app_port"/ $root_folder/config/nginx
sed -i s/"test\.regovar\.org"/"$public_host"/ $root_folder/config/nginx
echo -e "\r${GREEN}Done${NC}: Generating nginx config file"

# apply config
if test "$(ls -A "/etc/nginx/sites-available/regovar")"; then
    sudo mv -f /etc/nginx/sites-available/regovar /etc/nginx/sites-available/regovar.bak
fi
sudo mv -f $root_folder/config/nginx /etc/nginx/sites-available/regovar
ln -s /etc/nginx/sites-available/regovar $root_folder/config/nginx
sudo ln -s /etc/nginx/sites-available/regovar /etc/nginx/sites-enabled/regovar
sudo chown $EUID:$EUID $root_folder/config/nginx
/etc/init.d/nginx restart




# =======================================================================================
# Build regovar container
# =======================================================================================
echo -e "\nBuilding docker containers:\n======================================================================================="
cd $root_folder/config
docker-compose -f regovar.yml down
docker-compose -f regovar.yml up -d
# regovar container have been created and installed but already exited as installation is
# done. So we saves modified container state into a new image to be able to start/run it  
# with a different entry point
# docker commit regovar regovar_app
# docker run -ti --entrypoint=sh regovar_app

echo -e "${GREEN}Done${NC}: Docker containers ready"




# =======================================================================================
# Install regovar application and database
# =======================================================================================
echo -e "\nDatabase creation:\n======================================================================================="
curl http://hgdownload.soe.ucsc.edu/goldenPath/hg19/database/refGene.txt.gz | gunzip > $root_folder/databases/hg19/refGene.txt
curl http://hgdownload.soe.ucsc.edu/goldenPath/hg38/database/refGene.txt.gz | gunzip > $root_folder/databases/hg38/refGene.txt
docker exec regovar_pg mkdir /var/regovar/install
docker cp $git_path/install/create_all.sql regovar_pg:/var/regovar/install/create_all.sql
docker cp $git_path/install/install_hg19.sql regovar_pg:/var/regovar/install/install_hg19.sql
docker cp $git_path/install/install_hg38.sql regovar_pg:/var/regovar/install/install_hg38.sql
echo "Create Database ------------------"
docker exec regovar_pg psql -U postgres -c "DROP DATABASE IF EXISTS $db_name"
docker exec regovar_pg psql -U postgres -c "CREATE DATABASE $db_name OWNER $db_user"
docker exec regovar_pg psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""
docker exec regovar_pg psql -U $db_user -d $db_name -f /var/regovar/install/create_all.sql
echo "Import Hg19 ----------------------"
docker exec regovar_pg psql -U $db_user -d $db_name -f /var/regovar/install/install_hg19.sql
echo "Import Hg38 ----------------------"
docker exec regovar_pg psql -U $db_user -d $db_name -f /var/regovar/install/install_hg38.sql
echo -e "${GREEN}Done${NC}: Database created"

echo -e "\nRegovar application installation:\n======================================================================================="
# TO copy file into the regovar_app container we need to start it and keep it alive any time
#docker start regovar_app -t make update_hpo
echo -e "${GREEN}Done${NC}: Regovar application installation"




# =======================================================================================
# Test
# =======================================================================================
echo -e "\n${GREEN}Installation completed!${NC} Enjoy :)"
docker exec regovar_app -d make start
echo -e "Start Regovar application"
echo "  $ make start: to start or restart the server"
echo "  $ make stop: to kill the server"
echo "  $ make debug: to start the server with an interactive terminal"
echo "  $ make update_hpo: to update hpo data (server must be stopped to avoid data corruption)"





                                   