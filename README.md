# EC2接続時に必ず実行すること
    eval "$(ssh-agent -s)"
    ssh-add ~/.ssh/github-key