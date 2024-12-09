const URLS = {
    "user": "/v1/user",
    "traveler": "/v1/traveler",
    "itinerary": "/v1/itinerary"
}

const CITY_DESCRIPTION_MAX_LENGTH = 250;

const ACCESS_TOKEN = "access_token";
const REFRESH_TOKEN = "refresh_token";
const REFRESH_TOKEN_TIME = 1000 * 60 * 13;
let scheduled_refresh = null;



function set_tokens(data) {
    localStorage.setItem(ACCESS_TOKEN, data.response.access_token);
    localStorage.setItem(REFRESH_TOKEN, data.response.refresh_token);

    if(scheduled_refresh) clearTimeout(scheduled_refresh);

    setTimeout(() => refresh_token(), REFRESH_TOKEN_TIME);
}

function get_access_token() {
    const access_token = localStorage.getItem(ACCESS_TOKEN);

    if(!access_token) {
        go_to_login();
    }

    return access_token;
}

function get_refresh_token() {
    const refresh_token = localStorage.getItem(REFRESH_TOKEN);

    if(!refresh_token) {
        go_to_login();
    }

    return refresh_token;
}

function refresh_token() {
    fetch(
        `${URLS.user}/refresh-token`,
    {
            "method": "POST",
            "headers": {
                "Content-Type": "application/json"
            },
            "body": JSON.stringify({
                "refresh_token": get_refresh_token()
            })
        }
    )
    .then(response => {
        if(!response.ok) go_to_login();

        return response.json();
    })
    .then(set_tokens)
    .catch(console.log)
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

function decode_budget(budget) {
    switch (budget) {
        case "LOW": return "Low budget";
        case "MEDIUM": return "Medium budget";
        case "HIGH": return "High budget";
        default: throw new Error("wrong budget value!");
    }
}

function decode_travelling_with(travelling_with) {
    switch (travelling_with) {
        case "SOLO": return "Solo trip";
        case "COUPLE": return "Couple trip";
        case "FAMILY": return "Family trip";
        case "FRIENDS": return "Friends trip";
        default: throw new Error("wrong travelling with value!");
    }
}

function decode_interested_in(activity) {
    switch (activity) {
        case "BEACH": return "Beaches";
        case "CITY_SIGHTSEEING": return "City sightseeing";
        case "OUTDOOR_ADVENTURES": return "Outdoor adventures";
        case "FESTIVAL": return "Festival";
        case "FOOD_EXPLORATION": return "Food exploration";
        case "NIGHTLIFE": return "Nightlife";
        case "SHOPPING": return "Shopping";
        case "SPA_WELLNESS": return "Spa & Wellness";
        default: throw new Error("wrong activity value!");
    }
}

function decode_saved_by(saved_by) {
    if(saved_by < 100) return saved_by;
    else if(saved_by > 100 && saved_by <= 999) return "100+";
    else if (saved_by > 1_000 && saved_by <= 9_999) return "1k+";
    else if(data.saved_by > 10_000 && data.saved_by <= 99_999) return "10k+";
    else if (data.saved_by > 100_000 && data.saved_by <= 999_999) return "100k+";

    return "1M+";
}

function go_to_dashboard() {
    fetch(
        `${URLS.user}/dashboard`,
        {
            "headers": {
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
            set_tokens(data);
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
            //go_to_login();
        }

        return response.json();
    })
    .then(data => {
        $("#first_name").text(data.response.first_name)
    })
    .catch(console.log);
}
function get_most_saved_itineraries() {
    const access_token = get_access_token();
    return fetch(
        `${URLS.itinerary}/most-saved`,
        {
            "method": "GET",
            "headers": {"Authorization": `Bearer ${access_token}`}
        }
    )
    .then(response => {
        if(!response.ok) {
            throw new Error("error while retrieving most saved itineraries!");
        }

        return response.json();
    })
    .then(data => {
        handle_most_saved_itinerary(data.response[0]);
        handle_itinerary_carousel(data.response);
        console.log(data);
    });
}

function handle_most_saved_itinerary(data) {
    $("span#top_itinerary_country").each(function() { $(this).text(data.country) });
    $("span#top_itinerary_city").each(function() { $(this).text(data.city) });
    $("p#top_itinerary_description").each(function() { $(this).text(data.description) });
    $("span#top_itinerary_duration").each(function() { $(this).text(`${data.duration} day${data.duration > 1 ? "s" : ""}`) });
    $("span#top_itinerary_travelling_with").each(function() { $(this).text(decode_travelling_with(data.travelling_with)) });
    $("span#top_itinerary_budget").each(function() { $(this).text(decode_budget(data.budget)) });
    $("span#top_itinerary_saves").each(function() { $(this).text(decode_saved_by(data.saved_by)) });
    $("img#top_itinerary_img").each(function () {
        $(this).attr("src", data.image.urls.regular);
        $(this).attr("alt", data.image.alt_description);
    });

    $("div#interested_in_container").each(function() {
        data.interested_in.forEach((activity, idx) => {
            $(this).append(
                `<span class="bg-white border border-1 border-black rounded-pill px-2 py-1 ${idx === 0 ? "" : "ms-2"}">${decode_interested_in(activity)}</span>`
            );
        })
    })


    $("button#top_itinerary_find_out").each(function() { $(this).on("click", () => window.location.href=`/itinerary/detail/${data.id}`) });

    /*$("#top_itinerary_country").text(data.country);
    $("#top_itinerary_city").text(data.city);
    $("#top_itinerary_description").text(data.description);
    $("#top_itinerary_duration").text(`${data.duration} day${data.duration > 1 ? "s" : ""}`);
    $("#top_itinerary_travelling_with").text(decode_travelling_with(data.travelling_with));
    $("#top_itinerary_budget").text(decode_budget(data.budget));
    $("#top_itinerary_saves").text(decode_saved_by(data.saved_by));
    $("#top_itinerary_img")
        .attr("src", data.image.urls.small)
        .attr("alt", data.image.alt_description);

    data.interested_in.forEach((activity, idx) => {
        $("#interested_in_container").append(
            `<span class="bg-white border border-1 border-black rounded-pill px-2 py-1 ${idx === 0 ? "" : "ms-2"}">${decode_interested_in(activity)}</span>`
        );
    })


    $("#top_itinerary_find_out").on("click", () => window.location.href=`/itinerary/detail/${data.id}`);*/
}

function handle_itinerary_carousel(data) {
    data.forEach((itinerary, itinerary_num) => {
        if(itinerary_num > 0) {
            $('div#itinerary_carousel_container').each(function() {
                const country_city = `${itinerary.country}, ${itinerary.city}`;
                $(this).append(
                    `<div id="itinerary_carousel_${itinerary_num}" class="carousel-item ${itinerary_num === 1 ? "active": ""} pb-1" data-title="${country_city}">
                        <img class="d-none d-2xl-block w-100 object-fit-cover" height="290"
                             src="${itinerary.image.urls.regular}" alt="${itinerary.image.alt_description}"/>
                        <img class="d-none d-xxl-block d-2xl-none w-100 object-fit-cover" height="215"
                             src="${itinerary.image.urls.regular}" alt="${itinerary.image.alt_description}"/>
                        <img class="d-block d-xxl-none w-100 object-fit-cover" height="390"
                             src="${itinerary.image.urls.regular}" alt="${itinerary.image.alt_description}"/>
                        <div class="d-none d-sm-block">
                            <div class="row mt-2">
                                <div class="col-4">
                                    <h2 class="d-none d-sm-block d-md-none d-xxl-block ${country_city.length > 20 ? "fs-26" : "fs-32"}">${country_city}</h2>
                                    <h2 class="d-none d-md-block d-xxl-none fs-40">${country_city}</h2>
                                </div>
                                <div class="col-8">
                                    <p class="d-none d-sm-block d-md-none d-xxl-block fs-14 m-0">${itinerary.description.length > CITY_DESCRIPTION_MAX_LENGTH ? itinerary.description.substring(0, CITY_DESCRIPTION_MAX_LENGTH - 1) + "..." : itinerary.description}</p>
                                    <p class="d-none d-md-block d-xxl-none m-0">${itinerary.description.length > CITY_DESCRIPTION_MAX_LENGTH ? itinerary.description.substring(0, CITY_DESCRIPTION_MAX_LENGTH - 1) + "..." : itinerary.description}</p>
                                </div>
                            </div>
                        </div>
                        <div class="d-block d-sm-none">
                            <div class="row mt-2">
                                <div class="col">
                                    <h2 class="fs-32">${country_city}</h2>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col">
                                    <p class="fs-14 m-0">${itinerary.description.length > CITY_DESCRIPTION_MAX_LENGTH ? itinerary.description.substring(0, CITY_DESCRIPTION_MAX_LENGTH - 1) + "..." : itinerary.description}</p>
                                </div>
                            </div>
                        </div>
                        <div class="row mt-2">
                            <div class="col-12">
                                <div id="itinerary_carousel_activity_2xl_${itinerary_num}" class="d-none d-sm-block d-xl-none d-2xl-block">
                                </div>
                                <div id="itinerary_carousel_activity_xxl_${itinerary_num}" class="d-none d-xxl-block d-2xl-none">
                                </div>
                            </div>
                        </div>
                    </div>`
                );

                itinerary.interested_in.forEach((activity, activity_num) => {
                    const decoded_activity = decode_interested_in(activity);
                    $('div#itinerary_carousel_activity_2xl_' + itinerary_num).each(function () {
                        $(this).append(
                            `<span class="bg-white border border-1 border-black rounded-pill px-2 py-1 ${activity_num > 0 ? "ms-1" : ""}">${decoded_activity}</span>`
                        );
                    })
                    $('div#itinerary_carousel_activity_xxl_' + itinerary_num).each(function () {
                        $(this).append(
                            `<span class="bg-white border border-1 border-black rounded-pill px-2 py-1 fs-14 ${activity_num > 0 ? "ms-1" : ""}">${decoded_activity}</span>`
                        );
                    })
                });
            });
        }
    });
}