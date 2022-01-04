var networkId = null;
var account = null;

window.addEventListener('load', async () => {
    if (window.ethereum) {
        ethereum.autoRefreshOnNetworkChange = false;
        window.web3 = new Web3(ethereum);
        try {
            await ethereum.enable();
            var accounts = await web3.eth.getAccounts();
            var option = {from: accounts[0]};
            networkId = web3.version.network;
            account = web3.eth.accounts[0];
        } catch (error) {
            // User denied account access...
        }
    } else if (window.web3) {
        window.web3 = new Web3(web3.currentProvider);
    } else {
        console.log('Non-Ethereum browser detected. You should consider trying MetaMask!');
    }
    if (document.getElementById('message') !== null) {
        sign(document.getElementById('message').innerText, function (err, signature) {
            if (err) console.error(err);
            document.getElementById('signature').innerText = signature;
        });
    }
    let button = document.getElementsByClassName('metamask_button')[0];
    if (button !== null) {
        button.firstElementChild.innerHTML = 'Addr: ' + web3.eth.accounts[0] + "<br>" + 'Network Id: ' + web3.version.network;
        button.style.cssText = "font-size:8pt;height:50px;margin-top:-10px";
        button.firstElementChild.style.cssText="padding-bottom:5px";
    }
});

window.addEventListener('load', function () {
    setInterval(function () {
        if (account !== null && (web3.eth.accounts[0] !== account || web3.version.network !== networkId)) {
            networkId = web3.version.network;
            account = web3.eth.accounts[0];
            location.reload(true);
        }
        else {
            networkId = web3.version.network;
            account = web3.eth.accounts[0];
        }
    }, 200)
});


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

function signAdmin(message, callback) {
    console.log(message);
    var signer = web3.eth.defaultAccount;
    message_hash = web3.sha3(
        '\u0019Ethereum Signed Message:\n' +
        message.length.toString() +
        message
    );
    web3.personal.sign(message, signer, callback);
}

function withdraw_sign_and_submit(element, message) {
    signAdmin(message, function (err, signature) {
        if (err) console.error(err);
        element.parentElement.getElementsByClassName('signature')[0].value = signature;
        element.parentElement.getElementsByClassName('user_address')[0].value = web3.eth.accounts[0]
        element.parentElement.submit();
    });
}