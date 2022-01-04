top text should be "Enter referral code to access the platform"

Text bellow referral number field should be : "Don't have referral code ? No problem, click here to learn how to obtain one, or join us on Telegram to get more info."

Telegram button should be the same color as "join" button, and the text should be "Join us on Telegram"


# Sitxex backend project

### Deployment
- git clone https://DW365@bitbucket.org/taddevelop/stixex_backend.git
- sudo apt update
- sudo apt install redis-server
- sudo nano /etc/redis/redis.conf
- Set `supervised systemd`
- sudo apt install postgresql postgresql-contrib
- sudo apt install build-essential libpq-dev
- cd stixex_backend/
- sudo apt install python3-dev python3-venv
- python3 -m venv venv
- . venv/bin/activate
- pip install -r requirements.txt
- sudo -u postgres psql
- create database stixex;
- ctrl+D
- sudo apt install nginx
- uvicorn app.api:app
- Configure nginx and supervisor

### Example nginx conf

```
server {
        listen 7000;

        server_name _;

        location ~* \.io {
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header Host $http_host;
            proxy_set_header X-NginX-Proxy false;

            proxy_pass http://localhost:8000;
            proxy_redirect off;

            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
        location / {
            proxy_pass http://localhost:8000;
        }
}
server {
        listen 7001;

        server_name _;

        location / {
        	proxy_pass http://localhost:8001;
    }
}

server {
        listen 80;

        server_name _;

        location / {
            root /home/ubuntu/stixex_frontend;
            index index.html;
        }
}
```

### Example supervisor conf

```
[program:stixex_api]
environment=PYTHONPATH=/home/wstar/Downloads/done/stixex_backend
command=/home/wstar/Downloads/done/stixex_backend/venv/bin/uvicorn app.api:app --port=8000
directory=/home/wstar/Downloads/done/stixex_backend/app
user=wstar
autostart=false
autorestart=true

redirect_stderr=true
stdout_logfile=/home/wstar/Downloads/done/stixex_backend/logs/api.log
stdout_logfile_backups=5

[program:stixex_admin]
environment=PYTHONPATH=/home/wstar/Downloads/done/stixex_backend
command=/home/wstar/Downloads/done/stixex_backend/venv/bin/python admin.py
directory=/home/wstar/Downloads/done/stixex_backend/app
user=wstar
autostart=false
autorestart=true

redirect_stderr=true
stdout_logfile=/home/wstar/Downloads/done/stixex_backend/logs/admin.log
stdout_logfile_backups=5

[program:stixex_bet_checker]
environment=PYTHONPATH=/home/wstar/Downloads/done/stixex_backend
command=/home/wstar/Downloads/done/stixex_backend/venv/bin/python bet_checker.py
directory=/home/wstar/Downloads/done/stixex_backend/app
user=wstar
autostart=false
autorestart=true

redirect_stderr=true
stdout_logfile=/home/wstar/Downloads/done/stixex_backend/logs/bet_checker.log
stdout_logfile_backups=5

[program:stixex_listener]
environment=PYTHONPATH=/home/wstar/Downloads/done/stixex_backend
command=/home/wstar/Downloads/done/stixex_backend/venv/bin/python listener.py 4
directory=/home/wstar/Downloads/done/stixex_backend/app
user=wstar
autostart=false
autorestart=true

redirect_stderr=true
stdout_logfile=/home/wstar/Downloads/done/stixex_backend/logs/listener.log
stdout_logfile_backups=5
```

### Example request signing
```
let message = "arg1|arg2|arg3" # In alphabet order
function sign(message, callback) {
    console.log(message);
    var signer = web3.eth.defaultAccount;
    var hex = '';
    for(var i=0;i<message.length;i++) {
        hex += ''+message.charCodeAt(i).toString(16)
    }
    var hexMessage = "0x" + hex;
    web3.personal.sign(hexMessage, signer, callback);
}
```
### Example websocket connection
```
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Websocket Example</title>
</head>
<body>
<script src="//cdnjs.cloudflare.com/ajax/libs/socket.io/2.2.0/socket.io.js"
        integrity="sha256-yr4fRk/GU1ehYJPAs8P4JlTgu0Hdsp4ZKrx8bDEDC3I=" crossorigin="anonymous"></script>
<script type="text/javascript" charset="utf-8">
    var socket = io('http://localhost:8000', {
        path: '/sio/socket.io',
        transports: ['websocket'],
    });
    socket.on('connect', function () {
        console.log("Connected");
        socket.emit('roomJoin', {roomName: '0xdD82B8F6194681d641CA3Cba6a83E56A3cE66A4f-4'})
    });
    socket.on('my event', function (msg_event) {
        console.log(msg_event);
    });
</script>
</body>
</html>
```