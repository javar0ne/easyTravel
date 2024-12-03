const URLS = {
    "user": "/v1/user",
    "traveler": "/v1/traveler"

}

const ACCESS_TOKEN = "access_token";
const REFRESH_TOKEN = "refresh_token";

function get_access_token() {
    const access_token = localStorage.getItem(ACCESS_TOKEN);

    if(!access_token) {
        go_to_dashboard();
    }

    return access_token;
}

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
        go_to_login();
    }
}

function go_to_login() {
    window.location.href='/login';
}

function go_to_dashboard() {
    fetch(
        `${URLS.user}/dashboard`,
        {
            "headers": {
                "Method": "GET",
                "Authorization": `Bearer ${localStorage.getItem(ACCESS_TOKEN)}`,
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

function show_error_toast(message) {
    $('#error_toast .toast-body').text(message);
    bootstrap.Toast.getOrCreateInstance($('#error_toast')).show();
}

function temporary_error_toast() {
    show_error_toast("There was a temporary error. Try again later!");
}

function credentials_error_toast() {
    show_error_toast("Incorrect email or password!");
}

function login() {
    let email = document.getElementById("email").value;
    let password = document.getElementById("password").value;

    if(email && validate_email(email) && password) {
        fetch(
            `${URLS.user}/login`,
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
                if(response.status === 401) {
                    credentials_error_toast();
                } else if(response.status === 400 || response.status === 500) {
                    temporary_error_toast();
                }
                throw new Error(data.response);
            }

            return data;
        })
        .then(data => {
            localStorage.setItem(ACCESS_TOKEN, data.response.access_token);
            localStorage.setItem(REFRESH_TOKEN, data.response.refresh_token);
            go_to_dashboard();
        })
        .catch(console.log);
    } else {
        show_error_toast("Insert username and password!");
    }
}

function validate_email(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function validate_birth_date(birth_date) {
    const converted_birth_date = new Date(birth_date);
    const today = new Date();
    return converted_birth_date <= today;
}

function validate_password(password, confirm_password) {
    return password && confirm_password && password === confirm_password;
}

function validate_traveler_signup() {
    const email = $("#email").val();
    const birth_date = $("#birth_date").val();
    const password = $("#password").val();
    const confirm_password = $("#confirm_password").val();

    const is_email_valid = validate_email(email);
    const is_birth_date_valid = validate_birth_date(birth_date);
    const is_password_valid = validate_password(password, confirm_password)

    if(!is_email_valid) show_error_toast("Email has not a valid format!");
    if(!is_birth_date_valid) show_error_toast("Birth date must not be greater than today!");
    if(!is_password_valid) show_error_toast("Passwords do not match!");

    return is_email_valid && is_birth_date_valid && is_password_valid;
}

function validate_traveler_signup_confirmation() {
    const min_one_activity_selected = $(".card").hasClass("selected");
    const is_token_valid = $("#token").val();

    if(!min_one_activity_selected) show_error_toast("Select at least one activity!");

    if(!min_one_activity_selected || !is_token_valid) return false;

    $('.card.selected').each(function () {
        const interested_in_container = $('#interested_in_container');
        const card_id = $(this).attr('id');

        interested_in_container.append(
            `<input type="hidden" name="interested_in" value="${card_id}">`
        );
    });

    return true;
}

function get_traveler() {
    const access_token = get_access_token();
    fetch(
        URLS.traveler,
        {
            // "headers": {"Content-Type": "application/json"}
            "method": "GET",
            "headers": {"Authorization": `Bearer ${access_token}`}
        }
    )
    .then(response => {
        if(!response.ok && response.status === 401) {
            go_to_login();
        }

        return response.json();
    })
    .then(data => {
        $("#first_name").text(data.response.first_name)
    })
    .catch(console.log);
}