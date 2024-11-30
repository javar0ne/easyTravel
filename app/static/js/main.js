const URLS = {
    "user": "/v1/user"
}

const ACCESS_TOKEN = "access_token"
const REFRESH_TOKEN = "refresh_token"

function check_token_existence() {
    const access_token = localStorage.getItem(ACCESS_TOKEN);
    const refresh_token = localStorage.getItem(REFRESH_TOKEN);

    if(access_token && refresh_token){
        go_to_dashboard();
    }
}

function check_token_existence_with_redirect() {
    const access_token = localStorage.getItem(ACCESS_TOKEN);
    const refresh_token = localStorage.getItem(REFRESH_TOKEN);

    if(!access_token || !refresh_token){
        window.location.href='/login';
    }
}

function go_to_dashboard() {
    fetch(
        URLS.user + "/dashboard",
        {
            "headers": {
                "Method": "GET",
                "Authorization": "Bearer " + localStorage.getItem(ACCESS_TOKEN),
                "Content-Type": "application/json"
            }
        }
    )
    .then(response => {
        let data = response.json();
        if(!response.ok && response.status === 401) {
           throw new Error("Unauthorized")
        }
        return data;
    })
    .then(data => window.location.href=data.response)
    .catch(console.log);
}

function login() {
    let email = document.getElementById("email").value;
    let password = document.getElementById("password").value;

    if(email && password) {
        fetch(
            URLS.user + "/login",
            {
                "method": "POST",
                "headers": {"Content-Type": "application/json"},
                "body": JSON.stringify({
                    "email": email,
                    "password": password
                })
            }
        )
        .then(response => {
            let data = response.json();
            if (!response.ok) {
                throw new Error(data.response);
            }

            return data;
        })
        .then(data => {
            localStorage.setItem(ACCESS_TOKEN, data.response.access_token);
            localStorage.setItem(REFRESH_TOKEN, data.response.refresh_token);
            go_to_dashboard()
        })
        .catch(console.log);
    }
}