#! /bin/bash
user=ndoportal
group=ndoportal
group2=ndologs
wanted_group_id=44444
wanted_group2_id=44443
wanted_user_id=44444
starting_user_id=$(cat /etc/passwd | grep ^$user: | cut -d: -f3)
echo $starting_user_id
starting_group_id=$(cat /etc/group | grep ^$group: | cut -d: -f3)
echo $starting_group_id
starting_group2_id=$(cat /etc/group | grep ^$group2: | cut -d: -f3)
echo $starting_group2_id
if [ "$starting_user_id" == "" ]; then
  echo "user $user does not exist"
else
  if [ "$wanted_user_id" != "$starting_user_id" ]; then

    echo "changing userid for $user from $starting_user_id to $wanted_user_id"
    service nginx stop
    service supervisord stop
    killall --wait --user $user
    usermod -u $wanted_user_id $user
    find / -regextype posix-extended -regex "/(sys|srv|proc)" -prune -o -user $starting_user_id -exec chown -h $user {} +
    service nginx start
    service supervisord start
  else
    echo "userid for $user is already $starting_user_id"
  fi
fi

if [ "$starting_group_id" == "" ]; then
  echo "group $group does not exist"
else
  if [ "$wanted_group_id" != "$starting_group_id" ]; then
    echo "changing group id for $group from $starting_group_id to $wanted_group_id"
    groupmod -g $wanted_group_id $group
    find / -regextype posix-extended -regex "/(sys|srv|proc)" -prune -o -group $starting_group_id -exec chgrp -h $group {} +
  else
    echo "groupid for $group is already $starting_group_id"
  fi
fi

if [ "$starting_group2_id" == "" ]; then
  echo "group2 $group2 does not exist"
else
  if [ "$wanted_group2_id" != "$starting_group2_id" ]; then
    echo "changing group2 id for $group2 from $starting_group2_id to $wanted_group2_id"
    groupmod -g $wanted_group2_id $group2
    find / -regextype posix-extended -regex "/(sys|srv|proc)" -prune -o -group $starting_group2_id -exec chgrp -h $group2 {} +
  else
    echo "groupid for $group2 is already $starting_group2_id"
  fi
fi




