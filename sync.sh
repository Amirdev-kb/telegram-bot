#!/data/data/com.termux/files/usr/bin/bash

git add .

echo "✍️ Enter commit message:"
read msg

if [ -z "$msg" ]
then
  msg="update"
fi

git commit -m "$msg"
git push

echo "✅ Synced to GitHub!"
