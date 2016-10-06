# https://docs.docker.com/engine/reference/commandline/dockerd/#/linux-configuration-file

# Set top-level variables
while read l; do    
	key=$(echo $l | cut -d : -f 1 | tr -d \" | tr - _);
    	value=$(echo $l | cut -d : -f 2 | sed 's/.$//');
     	echo docker_config_$key: $value;
done < json

# Set dictionary variable
echo "docker_config_full:"
while read l; do  
	key=$(echo $l | cut -d : -f 1 | tr -d \" | tr - _);
      	orig=$(echo $l | cut -d : -f 1);
      	echo "   "$orig: \"{{ docker_config_$key }}\";
done < json
