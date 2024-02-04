function focusOnInput(e) {
    input = document.getElementById('input');
    const end = input.value.length;
    input.focus();
    input.setSelectionRange(end, end);
}

function onKeyDown(e) {
    focusOnInput(e);
    input = document.getElementById('input');
    var keyCode = e.which;
    switch (keyCode)
    {
        case 8: // backspace
            if (input.value.length <= 2)
                e.preventDefault();
            break;
        case 13: // enter
            e.preventDefault();
            data = input.value.substr(2, input.value.length - 2)
            //console.log(data)
            if (data.length == 0)
                break;
            ws.send(data)
            input.value = '# ';
            focusOnInput();
            break;
        case 9: // tab
            input.value += ' ';
            e.preventDefault();
            break;
        case 40: // down arrow
        case 38: // up arrow
            e.preventDefault();
            break;
        case 32: // space
            if (input.value.length == 2)
                e.preventDefault();
            break;
        default:
            break;
    }
    focusOnInput()
}

function keepFocusOnInput() {
    var t = this;
    setTimeout(function(){
        t.focus();
    }, 100);
}

function clearInputScreen() {
    input = document.getElementById('input').value = '# ';
    focusOnInput();
}

function clearOutputScreen() {
    output = document.getElementById('output');
    output.innerHTML = '';
}

function initialize() {
    input = document.getElementById('input');
    output = document.getElementById('output');
    clearInputScreen();
    clearOutputScreen();
    scrollToBottom();
    input.addEventListener('blur', keepFocusOnInput);
}

function scrollToBottom() {
    output = document.getElementById('output');
    //window.scrollTo(0, output.scrollHeight);
    output.scrollTop = output.scrollHeight;
}

function executeScreenCommand(command) {
    switch (command) {
        case 'clear':
            clearOutputScreen();
            break;
        default:
            break;
    }
}

window.onresize = scrollToBottom

initialize();
const ws = new WebSocket('ws://localhost:8084');
let ws_connection = false;

ws.addEventListener('message', function(event) {
    data = event.data;
    if (data[0] == '\xff')
        executeScreenCommand(data.substr(1, data.length - 1));
    else {
        output = document.getElementById('output');
        output.innerHTML += data;
        scrollToBottom();
    }
})

ws.addEventListener('open', function(event) {
    output = document.getElementById('output');
    output.innerHTML = '<span style=\'color: #04E800\'>Connection with terminal established!</span><br>'
    scrollToBottom();
    ws_connection = true;
})

ws.addEventListener('close', function(event) {
    if (!ws_connection) {
        output.innerHTML = '<span style=\'color: #FF1900\'>Connection error: Couldn\'t reach the terminal.</span>';
    } else {
        output.innerHTML += '<br><span style=\'color: #FF1900\'>Lost connection with the terminal. Check server status and refresh the page.</span><br>';
        ws_connection = false;
    }
    scrollToBottom();
})