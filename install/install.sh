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
regovar_user="$(id -u):$(id -g)"
root_folder="/var/regovar"
random_key32=`cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1`
omim_key=""
public_host="test.regovar.org"
db_user="regovar"
db_pwd="regovar"
db_name="regovar"
docker_pg="regovar_pg"
docker_app="regovar_app"
docker_app_port=8500
docker_network="regovar_net"
install_choice=1


# =======================================================================================
# Ask user to set main config settings
# =======================================================================================
echo -e "${CYAN}\n __   ___  __   __             __  \n|__) |__  / _\` /  \ \  /  /\  |__) \n|  \ |___ \__) \__/  \/  /~~\ |  \ \n${NC}"
echo -e "This script will help you to install and configure regovar server.\nPlease answers to few questions.\n"
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

echo -n "3) Private 32 bits key used to encrypts cookies and security token (HTTPS) (default: random generation): "
read answer
if [ -n "$answer" ]; then
    random_key32=$answer
fi

echo -n "4) OMIM API key: "
read answer
if [ -n "$answer" ]; then
    omim_key=$answer
fi

echo -n "5) Public hostname (default: $public_host): "
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

echo "7) Docker database container:"
echo -n "   - container's name: (default: $docker_pg): "
read answer
if [ -n "$answer" ]; then
    docker_pg=$answer
fi


echo "8) Docker application container:"
echo -n "   - container's name: (default: $docker_app): "
read answer
if [ -n "$answer" ]; then
    docker_app=$answer
fi
echo -n "   - application port: (default: $docker_app_port): "
read answer
if [ -n "$answer" ]; then
    docker_app_port=$answer
fi

echo -n "9) Docker private network name (default: $docker_network): "
read answer
if [ -n "$answer" ]; then
    docker_network=$answer
fi



# =======================================================================================
# Resume user settings
# =======================================================================================
echo -e "\nThanks!\nWe will generate for you the configuration files with provided information:"
echo -e " - ${WHITE}HOST_USER:${NC}\t\t$regovar_user"
echo -e " - ${WHITE}HOST_ROOT:${NC}\t\t$root_folder"

echo -e " - ${WHITE}DEBUG:${NC}\t\t$debug"
echo -e " - ${WHITE}PRIVATE_KEY32:${NC}\t$random_key32"
echo -e " - ${WHITE}OMIM_API_KEY:${NC}\t$omim_key"
echo -e " - ${WHITE}HOST_P:${NC}\t\t$public_host"
echo -e " - ${WHITE}DATABASE_USER:${NC}\t$db_user"
echo -e " - ${WHITE}DATABASE_PWD:${NC}\t$db_pwd"
echo -e " - ${WHITE}DATABASE_NAME:${NC}\t$db_name"

echo -e " - ${WHITE}DOCKER_DB_NAME:${NC}\t$docker_pg"
echo -e " - ${WHITE}DOCKER_APP_NAME:${NC}\t$docker_app"
echo -e " - ${WHITE}DOCKER_APP_PORT:${NC}\t$docker_app_port"
echo -e " - ${WHITE}DOCKER_NETWORK:${NC}\t$docker_network"




# =======================================================================================
# Preparing files repository on HOST
# =======================================================================================
echo -e "\nGenerating config files:\n======================================================================================="
if [ -e "$root_folder" ]
then
    echo -e "${YELLOW}Warning:${NC} The directory $root_folder already exists."
    echo -e "         1) Erase all content of $root_folder and continue (New install)"
    echo -e "         2) Erase only app folder and keep data of $root_folder (Update application)"
    echo -e "         3) Abord (Default, cancel installation)"
    echo -e -n "Your choice [1|2|3]: "
    read install_choice
fi

if [ "1" == "$install_choice" ]
then
    sudo rm -Rf $root_folder
    sudo mkdir -p ${root_folder}/{config,cache,downloads,files,pipelines,jobs,pgdata,databases/hg19,databases/hg38}
    install_choice=1
elif [ "2" == "$install_choice" ]
then
    sudo rm -Rf $root_folder/app
    install_choice=2
else
    echo -e "  ${RED}Error:${NC} Installation canceled"
    exit 1
fi

sudo chown -R $regovar_user ${root_folder}
echo -e "${GREEN}Done:${NC} Regovar folders created on HOST: $root_folder"

ln -s $git_path/regovar $root_folder/app
cp $git_path/requirements.txt $root_folder/config/requirements.txt
cp $git_path/requirements-dev.txt $root_folder/config/requirements-dev.txt



# =======================================================================================
# Generating: regovar_app Dockerfile
# =======================================================================================
# conver / into \/
sed_root_folder=${root_folder//\//\\/}

echo -e -n "${YELLOW}In progress${NC}: Generating Dockerfile for $docker_app docker image"
cp docker/Dockerfile $root_folder/config/Dockerfile
echo -e "\r${GREEN}Done${NC}: Generating Dockerfile for $docker_app docker image"




# =======================================================================================
# Generating: docker-compose
# =======================================================================================
echo -e -n "${YELLOW}In progress${NC}: Generating docker-compose file"
cp docker/docker-compose.yml $root_folder/config/regovar.yml
sed -i s/"{root_path}"/"$sed_root_folder"/g $root_folder/config/regovar.yml
sed -i s/"{git_path}"/"${git_path//\//\\/}"/g $root_folder/config/regovar.yml
sed -i s/"{regovar_user}"/"$regovar_user"/g $root_folder/config/regovar.yml
sed -i s/"{docker_pg}"/"$docker_pg"/g $root_folder/config/regovar.yml
sed -i s/"{docker_app}"/"$docker_app"/g $root_folder/config/regovar.yml
sed -i s/"{regovar_port}"/"$docker_app_port"/g $root_folder/config/regovar.yml
sed -i s/"{docker_net}"/"$docker_network"/g $root_folder/config/regovar.yml
sed -i s/"{db_user}"/"$db_user"/g $root_folder/config/regovar.yml
sed -i s/"{db_pwd}"/"$db_pwd"/g $root_folder/config/regovar.yml
sed -i s/"{db_name}"/"$db_name"/g $root_folder/config/regovar.yml
echo -e "\r${GREEN}Done${NC}: Generating docker-compose file"




# =======================================================================================
# Generating: regovar config.py
# =======================================================================================
echo -e -n "${YELLOW}In progress${NC}: Generating regovar app python config file"
cp config/config.default.py $git_path/regovar/config.py
# conver / into \/ and . into \.
public_host=${public_host//\//\\/}
public_host=${public_host//\./\\.}
sed -i s/"regovar_pg"/"$docker_pg"/ $git_path/regovar/config.py
sed -i s/"regovar_docker_app"/"$docker_app"/ $git_path/regovar/config.py
sed -i s/"regovar_net"/"$docker_network"/ $git_path/regovar/config.py
sed -i s/"^\(\s*DEBUG\s*=\s*\)\(.*\)"/"\1$debug"/ $git_path/regovar/config.py
sed -i s/"^\(\s*PORT\s*=\s*\)\(.*\)"/"\1$docker_app_port"/ $git_path/regovar/config.py
sed -i s/"^\(\s*HOST_P\s*=\s*\"\)\(.*\)\(\".*\)"/"\1$public_host\3"/ $git_path/regovar/config.py
sed -i s/"^\(\s*PRIVATE_KEY32\s*=\s*\"\)\(.*\)\(\".*\)"/"\1$random_key32\3"/ $git_path/regovar/config.py
sed -i s/"^\(\s*OMIM_API_KEY\s*=\s*\"\)\(.*\)\(\".*\)"/"\1$omim_key\3"/ $git_path/regovar/config.py
sed -i s/"^\(\s*DATABASE_USER\s*=\s*\"\)\(.*\)\(\".*\)"/"\1$db_user\3"/ $git_path/regovar/config.py
sed -i s/"^\(\s*DATABASE_PWD\s*=\s*\"\)\(.*\)\(\".*\)"/"\1$db_pwd\3"/ $git_path/regovar/config.py
sed -i s/"^\(\s*DATABASE_NAME\s*=\s*\"\)\(.*\)\(\".*\)"/"\1$db_name\3"/ $git_path/regovar/config.py

ln -s $git_path/regovar/config.py $root_folder/config/config.py
echo -e "\r${GREEN}Done${NC}: Generating regovar app python config file"




# =======================================================================================
# Generating: regovar postgresql config file
# =======================================================================================
echo -e -n "${YELLOW}In progress${NC}: Generating regovar postgresql config file"
cp config/postgres.conf $root_folder/config/postgres.conf
echo -e "\r${GREEN}Done${NC}: Generating regovar postgresql config file"




# =======================================================================================
# Generating: nginx sites-availables file
# =======================================================================================
echo -e -n "${YELLOW}In progress${NC}: Generating nginx config file"
cp config/nginx $root_folder/config/nginx
sed -i s/"8500"/"$docker_app_port"/ $root_folder/config/nginx
sed -i s/"test\.regovar\.org"/"$public_host"/ $root_folder/config/nginx
echo -e "\r${GREEN}Done${NC}: Generating nginx config file"

# apply config
if [ -e "/etc/nginx/sites-enabled/regovar" ]
then
    sudo rm /etc/nginx/sites-enabled/regovar
fi
sudo ln -s $root_folder/config/nginx /etc/nginx/sites-enabled/regovar
sudo /etc/init.d/nginx restart





# =======================================================================================
# Generating: Makefile
# =======================================================================================
echo -e -n "${YELLOW}In progress${NC}: Generating Makefile"
cp docker/Makefile.in $git_path/regovar/Makefile

sed -i s/"{root_path}"/"$sed_root_folder"/g $git_path/regovar/Makefile
sed -i s/"{git_path}"/"${git_path//\//\\/}"/g $git_path/regovar/Makefile
sed -i s/"{regovar_user}"/"$regovar_user"/g $git_path/regovar/Makefile
sed -i s/"{docker_pg}"/"$docker_pg"/g $git_path/regovar/Makefile
sed -i s/"{docker_app}"/"$docker_app"/g $git_path/regovar/Makefile
sed -i s/"{regovar_port}"/"$docker_app_port"/g $git_path/regovar/Makefile
sed -i s/"{docker_net}"/"$docker_network"/g $git_path/regovar/Makefile
sed -i s/"{db_user}"/"$db_user"/g $git_path/regovar/Makefile
sed -i s/"{db_name}"/"$db_name"/g $git_path/regovar/Makefile

ln -s $git_path/regovar/Makefile $root_folder/config/Makefile
echo -e "\r${GREEN}Done${NC}: Generating Makefile"





# =======================================================================================
# Build regovar container
# =======================================================================================
echo -e "\nBuilding docker containers:\n======================================================================================="
cd $root_folder/config
docker-compose -f regovar.yml down
docker-compose -f regovar.yml up -d


echo -e "${GREEN}Done${NC}: Docker containers ready"



# =======================================================================================
# Install regovar application and database
# =======================================================================================
echo -e "\nDatabase creation:\n======================================================================================="
if [ 1 == $install_choice ]
then
    curl -L ftp://ftp.1000genomes.ebi.ac.uk/vol1/ftp/technical/reference/human_g1k_v37.fasta.gz | gunzip > $root_folder/databases/GRCh37/human_g1k_v37.fasta
    curl -L http://hgdownload.soe.ucsc.edu/goldenPath/hg38/database/refGene.txt.gz | gunzip > $root_folder/databases/hg38/refGene.txt
    curl -L http://hgdownload.soe.ucsc.edu/goldenPath/hg38/database/refGene.txt.gz | gunzip > $root_folder/databases/hg38/refGene.txt
    docker exec $docker_pg mkdir /tmp/install
    docker cp $git_path/install/create_all.sql $docker_pg:/tmp/install/create_all.sql
    docker cp $git_path/install/install_hg19.sql $docker_pg:/tmp/install/install_hg19.sql
    docker cp $git_path/install/install_hg38.sql $docker_pg:/tmp/install/install_hg38.sql
    echo "Create Database ------------------"
    docker exec $docker_pg psql -U postgres -c "DROP DATABASE IF EXISTS $db_name"
    docker exec $docker_pg psql -U postgres -c "CREATE DATABASE $db_name OWNER $db_user"
    docker exec $docker_pg psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""
    docker exec $docker_pg psql -U $db_user -d $db_name -f /tmp/install/create_all.sql
    echo "Import Hg19 ----------------------"
    docker exec $docker_pg psql -U $db_user -d $db_name -f /tmp/install/install_hg19.sql
    echo "Import Hg38 ----------------------"
    docker exec $docker_pg psql -U $db_user -d $db_name -f /tmp/install/install_hg38.sql
    echo -e "${GREEN}Done${NC}: Database created"
else
    echo -e "${GREEN}Done${NC}: Using existing database (Update install mode)"
fi

echo -e "\nRegovar application installation:\n======================================================================================="
# TO copy file into the regovar_app container we need to start it and keep it alive any time
#docker start regovar_app -t make update_hpo
echo -e "${GREEN}Done${NC}: Regovar application installation"




# =======================================================================================
# Test
# =======================================================================================
echo -e "\n${GREEN}Installation completed!${NC} Enjoy :)"
echo -e "Start Regovar application (go to $root_folder/app first)"
echo "  $ make start: to start or restart the server"
echo "  $ make stop: to kill the server"
echo "  $ make debug: to start the server with an interactive terminal"
echo "  $ make update_hpo: to update hpo data (server must be stopped to avoid data corruption)"





                                   
