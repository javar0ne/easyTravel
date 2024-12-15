const URLS = {
    "user": "/v1/user",
    "traveler": "/v1/traveler",
    "itinerary": "/v1/itinerary",
    "organization": "/v1/organization",
    "event": "/v1/event",
    "rest_countries": "https://restcountries.com/v3.1"
}

const CITY_DESCRIPTION_MAX_LENGTH = 300;
const BY_ACTIVITIES_CITY_DESCRIPTION_MAX_LENGTH = 250;
const CAROUSEL_MAX_NUM_ACTIVITY = 3;

const ACCESS_TOKEN = "access_token";
const REFRESH_TOKEN = "refresh_token";
const REFRESH_TOKEN_TIME = 1000 * 60 * 13;
let scheduled_refresh = null;

const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))


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

function go_to_itinerary(id) {
    window.location.href=`/itinerary/detail/${id}`;
}

function show_error_toast(message) {
    $('#error_toast .toast-body').text(message);
    bootstrap.Toast.getOrCreateInstance($('#error_toast')).show();
}

function show_success_toast(message) {
    $('#success_toast .toast-body').text(message);
    bootstrap.Toast.getOrCreateInstance($('#success_toast')).show();
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

function capitalize(text) {
    return text.charAt(0).toUpperCase() + text.slice(1).toLowerCase();
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
        $("#login_btn").attr("disabled", true);
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
            $("#login_btn").removeAttr("disabled");
        })
        .catch(err => $("#login_btn").removeAttr("disabled"));
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

function validate_generate_itinerary() {
    const city = $("#city").val();
    const budget_selected = $("input[name='budget']:checked").length;
    const people_selected = $("input[name='travelling-with']:checked").length;
    const interested_in = $("input[name='interested-in']:checked").length;
    const start_date = $('#daterange').data('daterangepicker').startDate;
    const end_date = $('#daterange').data('daterangepicker').endDate;

    if(!city) {
        show_error_toast("City must not be empty!");
    }
    if(!start_date || !end_date) {
        show_error_toast("Start date and end date must not be empty!");
    } else if(end_date.diff(start_date, 'days') > 7) {
        show_error_toast("Start date and end date must differ by 7 days at most!");
    } else {
        $('#start_date').attr("value", start_date.format('YYYY-MM-DD'));
        $('#end_date').attr("value", end_date.format('YYYY-MM-DD'));
    }
    if(budget_selected === 0) {
        show_error_toast("At least one budget must be selected!");
    }
    if(people_selected === 0) {
        show_error_toast("At least one option of people must be selected!");
    }
    if(interested_in === 0) {
        show_error_toast("At least one activity must be selected!");

    }

    return city !== '' &&
        budget_selected > 0 &&
        people_selected > 0 &&
        interested_in > 0;
}

function get_traveler() {
    return fetch(
        URLS.traveler,
        {
            "method": "GET",
            "headers": {"Authorization": `Bearer ${get_access_token()}`}
        }
    )
}

function get_organization() {
    return fetch(
        URLS.organization,
        {
            "method": "GET",
            "headers": {"Authorization": `Bearer ${get_access_token()}`}
        }
    )
}

function get_full_traveler() {
    return fetch(
        `${URLS.traveler}/full`,
        {
            "method": "GET",
            "headers": {"Authorization": `Bearer ${get_access_token()}`}
        }
    )
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
    $("div#main_top_itinerary_img").each(function () {
        $(this).attr("style",`background-image: url('${data.image.urls.regular}'); background-size: cover; background-position: center;`)
    });

    $("div#interested_in_container").each(function() {
        data.interested_in.forEach((activity, idx) => {
            $(this).append(
                `<span class="bg-white border border-1 border-black rounded-pill d-inline-block mb-2 px-2 py-1 me-2">${decode_interested_in(activity)}</span>`
            );
        })
    })


    $("button#top_itinerary_find_out").each(function() { $(this).on("click", () => go_to_itinerary(data.id)) });
}

function handle_itinerary_carousel(data) {
    data.forEach((itinerary, itinerary_num) => {
        if(itinerary_num > 0) {
            $('div#itinerary_carousel_container').each(function() {
                const country_city = `${itinerary.country}, ${itinerary.city}`;
                $(this).append(
                    `<div id="itinerary_carousel_${itinerary_num}" class="carousel-item ${itinerary_num === 1 ? "active": ""} pb-1" data-title="${country_city}" onclick="go_to_itinerary('${itinerary.id}')" style="cursor:pointer;">
                        <img class="d-none d-2xl-block w-100 object-fit-cover" height="290"
                             src="${itinerary.image.urls.regular}" alt="${itinerary.image.alt_description}"/>
                        <img class="d-none d-xxl-block d-2xl-none w-100 object-fit-cover" height="250"
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
                                <div id="itinerary_carousel_activity_2xl_${itinerary_num}" class="d-none d-sm-block d-xxl-none d-2xl-block my-2">
                                </div>
                                <div id="itinerary_carousel_activity_xxl_${itinerary_num}" class="d-none d-xxl-block d-2xl-none my-2">
                                </div>
                            </div>
                        </div>
                    </div>`
                );

                itinerary.interested_in.forEach((activity, activity_num) => {
                    if(activity_num < CAROUSEL_MAX_NUM_ACTIVITY){
                        const decoded_activity = decode_interested_in(activity);
                        $('div#itinerary_carousel_activity_2xl_' + itinerary_num).each(function () {
                            $(this).append(
                                `<span class="bg-white border border-1 border-black rounded-pill d-inline-block px-2 py-1 me-2">${decoded_activity}</span>`
                            );
                        })
                        $('div#itinerary_carousel_activity_xxl_' + itinerary_num).each(function () {
                            $(this).append(
                                `<span class="bg-white border border-1 border-black rounded-pill px-2 py-1 d-inline-block fs-14 me-2">${decoded_activity}</span>`
                            );
                        })
                    }
                });
                if(itinerary.interested_in.length > CAROUSEL_MAX_NUM_ACTIVITY){
                     $('div#itinerary_carousel_activity_2xl_' + itinerary_num).append(
                         `<span class="fs-14">+ ${itinerary.interested_in.length - CAROUSEL_MAX_NUM_ACTIVITY} activity</span>`
                     );
                     $('div#itinerary_carousel_activity_xxl_' + itinerary_num).append(
                         `<span class="fs-14">+ ${itinerary.interested_in.length - CAROUSEL_MAX_NUM_ACTIVITY} activity</span>`
                     );
                }
            });
        }
    });
}

function get_itinerary_by_activity(activity, activity_selector) {
    fetch(
        `${URLS.itinerary}/search`,
        {
            "method": "post",
            "headers": {
                "Authorization": `Bearer ${get_access_token()}`,
                "Content-Type": "application/json"
            },
            "body": JSON.stringify({
                "interested_in": [`${activity}`],
                "page_size": 5,
                "page_number": 0
            })
        }
    )
    .then(response => {
        if(!response.ok) {
            throw new Error("error while retrieving itineraries by activity!");
        }

        return response.json();
    })
    .then(data => {
        $("#interested_in_activity_container").append(
            `
            <div id="${activity_selector}-section">
                <div class="row align-items-end mx-xxl-auto">
                    <div class="col">
                        <h2 class="d-none d-md-block mb-0 fs-40">${capitalize(activity).replace("_", " ")} itineraries</h2>
                        <h2 class="d-none d-sm-block d-md-none mb-0 fs-32">${capitalize(activity).replace("_", " ")} itineraries</h2>
                        <h2 class="d-block d-sm-none mb-0 fs-28">${capitalize(activity).replace("_", " ")} itineraries</h2>
                    </div>
                    <div class="col-3">
                        <div class="d-grid justify-content-end" onclick="window.location.href='/itinerary/search?interested_in=${activity}'" style="cursor: pointer">
                            <span class="d-none d-md-block fs-14 text-black">Show more</span>
                            <span class="d-block d-md-none fs-12 text-black">Show more</span>
                        </div>
                    </div>
                </div>
                <div id="activity_itinerary_carousel" class="row mt-5 justify-content-center mx-auto">
                </div>
            </div>
            `
        );

        data.response.content.forEach((itinerary, num) => {
            $(`#${activity_selector}-section #activity_itinerary_carousel`).append(
                `
                 <div class="p-0 col-12 col-md-6 col-lg-4 col-xl-3 col-xxl-2">
                    <div class="card border border-0 rounded-0 w-100" role="button" onclick="go_to_itinerary('${itinerary.id}')">
                      <img class="card-img-top rounded-0 w-100 object-fit-cover" height="381" src="${itinerary.image.urls.regular}" alt="${itinerary.image.alt_description}">
                      <div class="card-body px-1 py-2 rounded-0">
                        <p class="card-title fw-light fs-24">${itinerary.country}, <span class="fw-bold">${itinerary.city}</span></p>
                        <p class="card-text">${itinerary.description.length > BY_ACTIVITIES_CITY_DESCRIPTION_MAX_LENGTH ? itinerary.description.substring(0, BY_ACTIVITIES_CITY_DESCRIPTION_MAX_LENGTH - 1) + "..." : itinerary.description}</p>
                        <div class="row">
                            <div id="interested_in_itinerary_carousel_${num}" class="col"></div>
                        </div>
                      </div>
                    </div>
                </div>
                `
            );

            itinerary.interested_in.forEach((interested_in,activity_num) => {
                if(activity_num < CAROUSEL_MAX_NUM_ACTIVITY){
                    $(`#${activity_selector}-section #interested_in_itinerary_carousel_${num}`).append(
                        `<span class="bg-white border border-1 border-black rounded-pill px-2 py-1 d-inline-block mb-1 fs-14 me-2">${decode_interested_in(interested_in)}</span>`
                    )
                }
            })
            if(itinerary.interested_in.length > CAROUSEL_MAX_NUM_ACTIVITY){
                 $(`#${activity_selector}-section #interested_in_itinerary_carousel_${num}`).append(
                     `<span class="fs-14">+ ${itinerary.interested_in.length - CAROUSEL_MAX_NUM_ACTIVITY} activity</span>`
                 );
            }
        });
    })
}

function get_itinerary_by_activities() {
    get_itinerary_by_activity("BEACH", "beach");
    get_itinerary_by_activity("CITY_SIGHTSEEING", "city-sightseeing");
    get_itinerary_by_activity("OUTDOOR_ADVENTURES", "outdoor-adventures");
    get_itinerary_by_activity("FESTIVAL", "festival");
    get_itinerary_by_activity("FOOD_EXPLORATION", "food-exploration");
    get_itinerary_by_activity("NIGHTLIFE", "nightlife");
    get_itinerary_by_activity("SHOPPING", "shopping");
    get_itinerary_by_activity("SPA_WELLNESS", "spa-wellness");
}

function save_itinerary(itinerary_id) {
    fetch(
        `${URLS.itinerary}/save/${itinerary_id}`,
        {
            "method": "post",
            "headers": {
                "Authorization": `Bearer ${get_access_token()}`
            }
        }
    )
    .then(response => {
        if(!response.ok) {
            throw new Error("error while saving itinerary!");
        }

        const src = $("#save_itinerary img").attr("src");
        if(src.includes("saved")) {
            $("#save_itinerary img").attr("src", "../../static/svg/save.svg");
            show_success_toast("Itinerary removed from saved!");
        } else {
            $("#save_itinerary img").attr("src", "../../static/svg/saved.svg");
            show_success_toast("Itinerary saved!");
        }

    })
}

function get_itinerary_meta_detail(itinerary_id) {
    return fetch(
        `${URLS.itinerary}/meta/detail/${itinerary_id}`,
        {
            "method": "get",
            "headers": {
                "Authorization": `Bearer ${get_access_token()}`
            }
        }
    )
}

function download_itinerary(itinerary_id) {
    return fetch(
        `${URLS.itinerary}/download/${itinerary_id}`,
        {
            "method": "get",
            "headers": {
                "Authorization": `Bearer ${get_access_token()}`
            }
        }
    )
}

function handle_capital_search(event, autocomplete_element) {
    const city = event.target.value;
    if(city && city.length >= 2) {
        search_for_capital(city, autocomplete_element, event.target.id)
    } else {
        $(`#${autocomplete_element}`).empty();
        $(`#${autocomplete_element}`).css("z-index", "");
    }
}

function search_for_capital(city, autocomplete_element, element_id) {
    if(!city) throw new Error("city is null!");

    fetch(
        `${URLS.rest_countries}/capital/${encodeURIComponent(city)}?fields=capital,name,capitalInfo`
    ).then(response => {
        if(!response.ok) {
            throw new Error("error while retrieving capital");
        }

        return response.json();
    })
    .then(data => {
        $(`#${autocomplete_element}`).empty();
        data.forEach(element => {
            $(`#${autocomplete_element}`).append(`
                <div onclick="set_city('${autocomplete_element}', '${element_id}', '${element.capital[0]}', '${element.capitalInfo.latlng}')" class="ps-3 px-1 autocomplete-item">${element.name.common}, ${element.capital[0]}</div>
            `);

            $(`#${autocomplete_element}`).css("display", "");
        });
        $(`#${autocomplete_element}`).css("z-index", "999");
    })
}

function set_city(autocomplete_element, element_id, city, coordinates) {
    if(city) {
        $(`#${element_id}`).val(city);
        $(`#${autocomplete_element}`).empty();
        if($("#city_lat").length) $("#city_lat").val(coordinates.split(',')[0]);
        if($("#city_lng").length) $("#city_lng").val(coordinates.split(',')[1]);
    }
}

function generate_itinerary() {
    if(validate_generate_itinerary()) {
        const city = $("#city").val();
        const budget = $("input[name='budget']:checked").attr("value");
        const travelling_with = $("input[name='travelling-with']:checked").attr("value");
        const start_date = $("#start_date").attr("value");
        const end_date = $("#end_date").attr("value");
        const accessibility = $("#accessibility").prop("checked");
        const city_lat = $("#city_lat").val();
        const city_lng = $("#city_lng").val();

        let interested_in = []
        $("input[name='interested-in']:checked").each(function () {
          interested_in.push($(this).attr("value"));
        })

        fetch(
            `${URLS.itinerary}/request`,
            {
                "method": "post",
                "headers": {
                    "Authorization": `Bearer ${get_access_token()}`,
                    "Content-Type": "application/json"
                },
                "body": JSON.stringify({
                    "city": city,
                    "budget": budget,
                    "interested_in": interested_in,
                    "travelling_with": travelling_with,
                    "start_date": start_date,
                    "end_date": end_date,
                    "accessibility": accessibility
                })
            }
        )
        .then(response => {
            if(!response.ok && response.status === 401) {
                throw new Error("authentication error!");
            }

            return response.json();
        })
        .then(data => window.location.href=`/itinerary/request/${data.response.request_id}?lat=${city_lat}&lng=${city_lng}`);
    }

}

function find_city_meta(city) {
    fetch(
        `${URLS.itinerary}/city-meta`,
        {
            "method": "post",
            "headers": {
                "Authorization": `Bearer ${get_access_token()}`,
                "Content-Type": "application/json"
            },
            "body": JSON.stringify({
                "name": city
            })
        }
    )
    .then(response => {
        if(!response.ok && response.status === 401) {
            throw new Error("error while retrieving city meta!");
        }
        if(response.status === 204) {
            setTimeout(() => find_city_meta(city), 1000);
            throw new Error("city meta not ready yet!");
        }

        return response.json();
    })
    .then(data => {
        $("#city_img").attr("src", data.response.image.urls.regular);
        $("#city_img").attr("alt", data.response.image.alt_description);
        $("h1#city_country").each(function() { $(this).text(`${data.response.country}, ${data.response.name}`) });
        $("p#city_description").each(function() { $(this).text(data.response.description) });
    });
}

function get_itinerary_request(id, map) {
    fetch(
        `${URLS.itinerary}/request/${id}`,
        {
            "headers": {
                "Authorization": `Bearer ${get_access_token()}`,
            }
        }
    )
    .then(response => {
        if(!response.ok && response.status === 401) {
            throw new Error("error while retrieving city meta!");
        }

        return response.json();
    })
    .then(data => {
        let stages_counter = 0;
        let coordinates = [];
        if(data.response.status === "PENDING") {
            setTimeout(() => get_itinerary_request(id, map), 1000);
        } else {
            $("#actions_container").empty();
            $("#actions_container").append(`
            <a id="save_itinerary" href="#" data-bs-placement="bottom" data-bs-toggle="tooltip" data-bs-title="Save itinerary"><img class="img-fluid" src="../../static/svg/save-itinerary.svg" alt="save"></a>
            `);
            $("#save_itinerary").on("click", () => create_itinerary(`${data.response.id}`));
        }

        $("#details_container").empty();
        data.response.details.forEach(detail => {
            $("#details_container").append(`
            <div class="accordion" id="accordionDay${detail.day}">
              <div class="accordion-item border-0">
                <h2 class="accordion-header">
                  <button class="accordion-button accordion-flush border border-2 border-black bg-white rounded-0" type="button" data-bs-toggle="collapse" data-bs-target="#collapse${detail.day}" aria-expanded="true" aria-controls="collapse${detail.day}">
                    <p class="lh-1 mb-0">
                        <span class="d-none d-xl-block fw-medium fs-24">Day ${detail.day} </span>
                        <span class="d-block d-lg-none fw-medium fs-20">Day ${detail.day} </span>
                    </p>
                  </button>
                </h2>
                <div id="collapse${detail.day}" class="accordion-collapse collapse show" data-bs-parent="#collapse${detail.day}">
                  <div class="accordion-body">
                    <div id="stages_container_${detail.day}" class="row"></div>
                  </div>
                </div>
              </div>
            </div>
            `);

            detail.stages.forEach(stage => {
                stages_counter++;
                coordinates.push([stage.coordinates.lat, stage.coordinates.lng]);
                $(`#stages_container_${detail.day}`).append(`
                <div class="col-12">
                    <div class="row gap-0 border border-black">
                        <div class="col-12 p-2">
                            <div class="row">
                                <div class="col">
                                    <div class="d-flex gap-2 align-items-center">
                                        <div class="bg-black px-3 py-1">
                                            <span class="fw-bold text-white">${stages_counter}</span>
                                        </div>
                                        <span class="fw-medium">${stage.title}</span>
                                    </div>
                                </div>
                                <div class="d-none d-xl-block col">
                                    <div class="d-flex justify-content-end">
                                        <img src="../../../static/svg/clock.svg" alt="clock">
                                        <span class="fs-12 ms-1">${stage.avg_duration}</span>
                                    </div>
                                </div>
                            </div>
                            <div class="row mt-2">
                                <div class="col-12">
                                    <span class="text-muted fs-14">
                                        ${stage.description}
                                    </span>
                                </div>
                            </div>
                            <div class="d-block d-xl-none">
                                <div class="col">
                                    <div class="d-flex justify-content-end">
                                        <img src="../../../static/svg/clock.svg" alt="clock">
                                        <span class="fs-12 ms-1">${stage.avg_duration}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                `);

                L.marker(
                  [stage.coordinates.lat, stage.coordinates.lng],
                  {
                      title:stages_counter,
                      icon: L.icon({
                        iconUrl: `../../static/svg/pin-${stages_counter}.svg`,

                        iconSize:     [38, 95], // size of the icon
                        iconAnchor:   [22, 94], // point of the icon which will correspond to marker's location
                        popupAnchor:  [-3, -76] // point from which the popup should open relative to the iconAnchor
                      })
                  }
                ).addTo(map)
                .bindPopup(
                  `<p><b>${stage.title}</b></p>`
                )
                .on("mouseover", e => e.target.togglePopup())
                .on("mouseout", e => e.target.togglePopup());
            })
        })

        map.fitBounds(coordinates);
    });
}

function create_itinerary(request_id) {
    fetch(
        `${URLS.itinerary}/create/${request_id}`,
        {
            "method": "post",
            "headers": {
                "Authorization": `Bearer ${get_access_token()}`,
            }
        }
    )
    .then(response => {
        if(!response.ok && response.status === 401) {
            throw new Error("error while creating itinerary!");
        }

        return response.json();
    })
    .then(data => window.location.href=`/itinerary/detail/${data.response.id}`);
}

function search_itineraries() {
    let city = $("#nav_city").val();
    if(city && city.length > 0) {
        window.location.href = `/itinerary/search?city=${city}`;
    }
}

function check_search() {
    let location = $("#location").val();
    let people = $("#people").val();
    let budget = $("#budget").val();
    let activity = $("#activity").val();


    if(!location && !people && !budget && !activity) {
        show_error_toast("Select at least one filter");
        return false;
    }

    return true;
}

function get_upcoming_itineraries() {
    fetch(
        `${URLS.itinerary}/upcoming`,
        {
            "headers": {
                "Authorization": `Bearer ${get_access_token()}`
            }
        }
    )
    .then(response => {
        if(!response.ok && response.status === 401) {
            throw new Error("error while retrieving upcoming itineraries!");
        }

        return response.json();
    })
    .then(data => {
        data.response.forEach((itinerary, num) => {
            $("#upcoming_container").append(`
            <div class="col-12 px-md-5">
                <div id="itinerary${num}" class="card border-0 shadow mb-3 w-full">
                    <div class="row g-0">
                        <div class="col-12 col-sm-6">
                          <div class="card-body">
                              <div class="row align-items-center">
                                  <div class="col">
                                      <h5 class="d-none d-xxl-block card-title fs-36 fw-bold">${itinerary.country}, ${itinerary.city}</h5>
                                      <h5 class="d-none d-xl-block d-xxl-none card-title fs-28 fw-bold">${itinerary.country}, ${itinerary.city}</h5>
                                      <h5 class="d-none d-md-block d-xl-none card-title fs-24 fw-bold">${itinerary.country}, ${itinerary.city}</h5>
                                      <h5 class="d-block d-md-none card-title fs-20 fw-bold">${itinerary.country}, ${itinerary.city}</h5>
                                  </div>
                                  <div class="d-none d-lg-block col">
                                      <div class="d-flex justify-content-end">
                                          <span class="d-none d-xxl-block badge text-bg-dark lh-lg px-3 fs-14">${itinerary.days_from_start <= 0 ? "Ongoing" : `In ${itinerary.days_from_start} day${itinerary.days_from_start === 0 || itinerary.days_from_start > 1 ? "s" : ""}`}</span>
                                          <span class="d-none d-lg-block d-xxl-none badge text-bg-dark lh-lg px-3 fs-12">${itinerary.days_from_start <= 0 ? "Ongoing" : `In ${itinerary.days_from_start} day${itinerary.days_from_start === 0 || itinerary.days_from_start > 1 ? "s" : ""}`}</span>
                                      </div>
                                  </div>
                              </div>
                              <p class="d-none d-lg-block card-text fs-14">${moment(itinerary.start_date).format("D MMM YYYY")} - ${moment(itinerary.end_date).format("D MMM YYYY")}</p>
                              <p class="d-block d-lg-none card-text fs-12">${moment(itinerary.start_date).format("D MMM YYYY")} - ${moment(itinerary.end_date).format("D MMM YYYY")}</p>
                              <div class="row">
                                  <div class="col-12">
                                      <div class="d-flex mb-2 mb-xl-0">
                                          <img src="../../../static/svg/calendar.svg" alt="calendar">
                                          <span class="d-none d-xxl-block fs-20 px-2 py-1">${itinerary.duration} day${itinerary.duration > 1 ? "s" : ""}</span>
                                          <span class="d-none d-xl-block d-xxl-none fs-18 px-2 py-1">${itinerary.duration} day${itinerary.duration > 1 ? "s" : ""}</span>
                                          <span class="d-none d-lg-block d-xl-none fs-14 px-2 py-1">${itinerary.duration} day${itinerary.duration > 1 ? "s" : ""}</span>
                                          <span class="d-block d-lg-none fs-12 px-2 py-1">${itinerary.duration} day${itinerary.duration > 1 ? "s" : ""}</span>
                                      </div>
                                      <div class="d-flex mb-2 mb-xl-0">
                                          <img src="../../../static/svg/people-${itinerary.travelling_with.toLowerCase()}.svg" alt="people">
                                          <span class="d-none d-xxl-block fs-20 px-2 py-1">${decode_travelling_with(itinerary.travelling_with)}</span>
                                          <span class="d-none d-xl-block d-xxl-none fs-18 px-2 py-1">${decode_travelling_with(itinerary.travelling_with)}</span>
                                          <span class="d-none d-lg-block d-xl-none fs-14 px-2 py-1">${decode_travelling_with(itinerary.travelling_with)}</span>
                                          <span class="d-block d-lg-none fs-12 px-2 py-1">${decode_travelling_with(itinerary.travelling_with)}</span>
                                      </div>
                                      <div class="d-flex mb-2 mb-xl-0">
                                          <img src="../../../static/svg/budget-${itinerary.budget.toLowerCase()}.svg" alt="budget">
                                          <span class="d-none d-xxl-block fs-20 px-2 py-1">${decode_budget(itinerary.budget)}</span>
                                          <span class="d-none d-xl-block d-xxl-none fs-18 px-2 py-1">${decode_budget(itinerary.budget)}</span>
                                          <span class="d-none d-lg-block d-xl-none fs-14 px-2 py-1">${decode_budget(itinerary.budget)}</span>
                                          <span class="d-block d-lg-none fs-12 px-2 py-1">${decode_budget(itinerary.budget)}</span>
                                      </div>
                                  </div>
                              </div>
                              <div class="row mt-xl-4">
                                  <div id="activity_container_xxl" class="col-12 d-none d-xxl-block">
                                  </div>
                                  <div id="activity_container_xl" class="col-12 d-none d-xl-block d-xxl-none">
                                  </div>
                              </div>
                              <div class="d-none d-2xl-block">
                                  <div class="d-flex justify-content-between mt-3">
                                      <span><img src="${itinerary.is_public ? "../../static/svg/published.svg": "../../static/svg/publish.svg"}" alt="publish" id="img_publish" onclick="publish_itinerary('${itinerary.id}', 'itinerary${num}')" style="cursor: pointer"></span>
                                      <input type="hidden" id="is_public" value="${itinerary.is_public ? "true" : ""}">
                                      <button data-bs-toggle="modal" data-bs-target="#inviteTravelersModal" class="px-5 py-1 fs-20 rounded bg-secondary border-0 fw-medium">Invite travelers</button>
                                  </div>
                              </div>
                              <div class="d-none d-md-block d-2xl-none">
                                  <div class="d-flex justify-content-between mt-2 mt-xl-4 mt-xxl-4">
                                      <span><img src="${itinerary.is_public ? "../../static/svg/published.svg": "../../static/svg/publish.svg"}" alt="publish" id="img_publish" onclick="publish_itinerary('${itinerary.id}', 'itinerary${num}')" style="cursor: pointer"></span>
                                      <input type="hidden" id="is_public" value="${itinerary.is_public ? "true" : ""}">
                                      <button data-bs-toggle="modal" data-bs-target="#inviteTravelersModal" class="d-none d-xxl-block px-5 py-1 fs-20 rounded bg-secondary border-0 fw-medium">Invite travelers</button>
                                      <button data-bs-toggle="modal" data-bs-target="#inviteTravelersModal" class="d-none d-xl-block d-xxl-none px-5 py-1 fs-18 rounded bg-secondary border-0 fw-medium">Invite travelers</button>
                                      <button data-bs-toggle="modal" data-bs-target="#inviteTravelersModal" class="d-none d-lg-block d-xl-none px-5 py-1 fs-16 rounded bg-secondary border-0 fw-medium">Invite travelers</button>
                                      <button data-bs-toggle="modal" data-bs-target="#inviteTravelersModal" class="d-block d-lg-none px-5 py-1 fs-14 rounded bg-secondary border-0 fw-medium">Invite travelers</button>
                                  </div>
                              </div>
                              <div class="d-block d-md-none">
                                  <div class="d-flex justify-content-between mt-3">
                                      <span><img src="${itinerary.is_public ? "../../static/svg/published.svg": "../../static/svg/publish.svg"}" alt="publish" id="img_publish" onclick="publish_itinerary('${itinerary.id}', 'itinerary${num}')" style="cursor: pointer"></span>
                                      <input type="hidden" id="is_public" value="${itinerary.is_public ? "true" : ""}">
                                      <button data-bs-toggle="modal" data-bs-target="#inviteTravelersModal" class="px-5 py-1 fs-14 rounded bg-secondary border-0 fw-medium">Invite travelers</button>
                                  </div>
                              </div>
                          </div>
                        </div>
                        <div class="col-6 rounded-end" onclick="go_to_itinerary('${itinerary.id}')" style="background-image: url('${itinerary.image.urls.regular}'); background-size: cover; background-position: center; cursor: pointer"></div>
                    </div>
                </div>
            </div>
            `)

            itinerary.interested_in.forEach(activity => {
                $(`#itinerary${num} #activity_container_xxl`).append(`
                  <span class="bg-white border border-1 border-black rounded-pill px-2 py-1">${decode_interested_in(activity)}</span>
                `);

                $(`#itinerary${num} #activity_container_xl`).append(`
                  <span class="bg-white border border-1 border-black rounded-pill fs-14 px-2 py-1">${decode_interested_in(activity)}</span>
                `);
            });
        })
    })
}

function publish_itinerary(id, itinerary_element) {
    let is_public = Boolean($(`#${itinerary_element} #is_public`).val());
    is_public = !is_public;

    fetch(
        `${URLS.itinerary}/publish`,
        {
            "method": "post",
            "headers": {
                "Authorization": `Bearer ${get_access_token()}`,
                "Content-Type": "application/json"
            },
            "body": JSON.stringify({
                "id": id,
                "is_public": is_public
            })
        }
    )
    .then(response => {
        if(!response.ok && response.status === 401) {
            throw new Error("error while retrieving upcoming itineraries!");
        }

        return response;
    })
    .then(response => {
        if(!is_public) {
            $(`#${itinerary_element} #img_publish`).attr("src", "../../static/svg/publish.svg");
            show_success_toast("Itinerary unpublished successfully!");
        } else {
            $(`#${itinerary_element} #img_publish`).attr("src", "../../static/svg/published.svg");
            show_success_toast("Itinerary published successfully!");
        }
        $(`#${itinerary_element} #is_public`).val(`${is_public ? is_public : ""}`);
    })
}

function get_past_itineraries() {
    fetch(
        `${URLS.itinerary}/past`,
        {
            "headers": {
                "Authorization": `Bearer ${get_access_token()}`
            }
        }
    )
    .then(response => {
        if(!response.ok && response.status === 401) {
            throw new Error("error while retrieving upcoming itineraries!");
        }

        return response.json();
    })
    .then(data => {
        data.response.forEach(itinerary => {
            $("#past_container").append(`
            <div class="card border-0 mb-3" onclick="go_to_itinerary('${itinerary.id}')" style="cursor:pointer;">
              <div class="row g-3">
                <div class="col-4">
                  <img src="${itinerary.image.urls.small}" class="d-none d-sm-block object-fit-cover rounded" width="130" height="130" alt="${itinerary.image.alt_description}">
                  <img src="${itinerary.image.urls.small}" class="d-block d-sm-none object-fit-cover rounded" width="80" height="80" alt="${itinerary.image.alt_description}">
                </div>
                <div class="col-8">
                  <div class="d-none d-sm-block card-body">
                    <h5 class="d-none d-sm-block card-title">${itinerary.country}, ${itinerary.city}</h5>
                    <p class="card-text">
                        <small class="d-none d-sm-block text-body-secondary">${moment(itinerary.start_date).format("D MMM YYYY")} - ${moment(itinerary.end_date).format("D MMM YYYY")}</small>
                    </p>
                  </div>
                  <div class="d-block d-sm-none card-body py-1 px-0">
                    <h5 class="card-title fs-14 mb-0">${itinerary.country}, ${itinerary.city}</h5>
                    <p class="card-text mb-0">
                        <small class="text-body-secondary fs-12">${moment(itinerary.start_date).format("D MMM YYYY")} - ${moment(itinerary.end_date).format("D MMM YYYY")}</small>
                    </p>
                  </div>
                </div>
              </div>
            </div>
            `)
        })
    })
}

function update_traveler() {
    const name = $("#name").val();
    const old_name = $("#name").data("defaultValue");
    const surname = $("#surname").val();
    const old_surname = $("#surname").data("defaultValue");
    const email = $("#email").val();
    const old_email = $("#email").data("defaultValue");
    const date_of_birth = $("#date_of_birth").val();
    const old_date_of_birth = $("#date_of_birth").data("defaultValue");
    const currency = $("#currency").val();
    const old_currency = $("#currency").data("defaultValue");

    if(!name || !surname || !email || !validate_email(email) || !date_of_birth || !currency) {
        show_error_toast("Cannot update, all data are required!");
        return;
    }

    if(
        name === old_name &&
        surname === old_surname &&
        email === old_email &&
        date_of_birth === old_date_of_birth &&
        currency === old_currency
    ) {
        show_success_toast("No data to update!");
        return;
    }

    fetch(
        `${URLS.traveler}`,
        {
            "method": "put",
            "headers": {
                "Authorization": `Bearer ${get_access_token()}`,
                "Content-Type": "application/json"
            },
            "body": JSON.stringify({
                "email": email,
                "currency": currency,
                "first_name": name,
                "last_name": surname,
                "birth_date": date_of_birth,
                "interested_in": [],
                "phone_number": ""
            })
        }
    )
    .then(response => {
        if(!response.ok && response.status === 401) {
            go_to_login();
        }

        $("#name").data("defaultValue", name);
        $("#surname").data("defaultValue", surname);
        $("#email").data("defaultValue", email);
        $("#date_of_birth").data("defaultValue", date_of_birth);
        $("#currency").data("defaultValue", currency);

        show_success_toast("Successfully updated traveler!");
    })
}

function get_saved_itineraries() {
    fetch(
        `${URLS.itinerary}/saved`,
        {
            "method": "post",
            "headers": {
                "Authorization": `Bearer ${get_access_token()}`,
                "Content-Type": "application/json"
            },
            "body": JSON.stringify({
                "page_size": 10,
                "page_number": 0
            })
        }
    )
    .then(response => {
        if(!response.ok && response.status === 401) {
            go_to_login()
        }

        return response.json();
    })
    .then(data => {
        data.response.content.forEach((itinerary, num) => {
            $("#itineraries_container").append(`
            <div class="col-12 col-sm-6 col-md-6 col-xl-4 col-xxl-3 mb-5">
                <div class="card border border-0 rounded-0">
                    <img class="card-img-top rounded-0 w-100 object-fit-cover" height="336" src="${itinerary.image.urls.regular}"
                         alt="${itinerary.image.alt_description}" onclick="go_to_itinerary('${itinerary.id}')" style="cursor: pointer"/>
                    <div class="card-body px-1 py-2 rounded-0">
                        <h5 class="card-title fw-light m-0 fs-24">${itinerary.country}, <span class="fw-bold fs-24">${itinerary.city}</span></h5>
                        <p class="card-text text-muted fs-14">${moment(itinerary.start_date).format("D MMM YYYY")} - ${moment(itinerary.end_date).format("D MMM YYYY")}</p>
                        <span id="itinerary${num}_activities"></span>
                        <hr class="my-2"/>
                        <div class="d-flex" id="save_itinerary">
                            <a href="#" data-bs-placement="top" data-bs-toggle="tooltip" data-bs-title="Save itinerary"><img src="../../../static/svg/saved.svg" onclick="save_itinerary_and_update('${itinerary.id}')"/></a>
                        </div>
                    </div>
                </div>
            </div>    
            `)

            itinerary.interested_in.forEach(activity =>
                $(`#itinerary${num}_activities`).append(`
                    <span class="bg-white border border-1 border-black rounded-pill px-2 py-1 d-inline-block mb-1 fs-14">${decode_interested_in(activity)}</span>
                `)
            )
        })
    })
}

function save_itinerary_and_update(id) {
    save_itinerary(id);
    $("#itineraries_container").empty();
    get_saved_itineraries();
}

function validate_create_event() {
    const city = $("#location").val();
    const title = $("#title").val();
    const start_date = $('#daterange').data('daterangepicker').startDate;
    const end_date = $('#daterange').data('daterangepicker').endDate;
    const description = $("#description").val();
    const avg_duration = $("#avg_duration").val();
    const cost = $("#cost").val();

    let interested_in = []
    $("input[name='interested-in']:checked").each(function () {
      interested_in.push($(this).attr("value"));
    })

    if(!city) {
        show_error_toast("City required!")
        return false;
    }
    if(!title) {
        show_error_toast("Title required!")
        return false;
    }

    if(!start_date || !end_date) {
        show_error_toast("Start date and end date must not be empty!");
        return false;
    } else {
        $('#start_date').attr("value", start_date.format('YYYY-MM-DD'));
        $('#end_date').attr("value", end_date.format('YYYY-MM-DD'));
    }

    if(!description) {
        show_error_toast("Description required!")
        return false;
    }
    if(!avg_duration) {
        show_error_toast("Average duration required!")
        return false;
    }
    if(!cost) {
        show_error_toast("Cost required!")
        return false;
    }

    if(interested_in.length === 0) {
        show_error_toast("Activities required!")
        return false;
    }

    return true;
}

function create_event() {
    if(validate_create_event()) {
        const city = $("#location").val();
        const title = $("#title").val();
        const start_date = $('#start_date').attr("value");
        const end_date = $('#end_date').attr("value");
        const description = $("#description").val();
        const avg_duration = $("#avg_duration").val();
        const cost = $("#cost").val();
        const accessibility = $("#accessibility").prop("checked");

        let interested_in = []
        $("input[name='interested-in']:checked").each(function () {
            interested_in.push($(this).attr("value"));
        })

        fetch(
            `${URLS.event}`,
            {
                "method": "post",
                "headers": {
                    "Authorization": `Bearer ${get_access_token()}`,
                    "Content-Type": "application/json"
                },
                "body": JSON.stringify({
                    "city": city,
                    "title": title,
                    "description": description,
                    "cost": cost,
                    "avg_duration": avg_duration,
                    "accessible": accessibility,
                    "related_activities": interested_in,
                    "start_date": start_date,
                    "end_date": end_date
                })
            }
        )
        .then(response => {
            if(!response.ok && response.status === 401) {
                go_to_login();
            }

            return response.json();
        })
        .then(data => window.location.href=`/event/${data.response.id}`)
    }
}

function update_event(id) {
    if(validate_create_event()) {
        const city = $("#location").val();
        const title = $("#title").val();
        const start_date = $('#start_date').attr("value");
        const end_date = $('#end_date').attr("value");
        const description = $("#description").val();
        const avg_duration = $("#avg_duration").val();
        const cost = $("#cost").val();
        const accessibility = $("#accessibility").prop("checked");

        let interested_in = []
        $("input[name='interested-in']:checked").each(function () {
            interested_in.push($(this).attr("value"));
        })

        fetch(
            `${URLS.event}/${id}`,
            {
                "method": "put",
                "headers": {
                    "Authorization": `Bearer ${get_access_token()}`,
                    "Content-Type": "application/json"
                },
                "body": JSON.stringify({
                    "city": city,
                    "title": title,
                    "description": description,
                    "cost": cost,
                    "avg_duration": avg_duration,
                    "accessible": accessibility,
                    "related_activities": interested_in,
                    "start_date": start_date,
                    "end_date": end_date
                })
            }
        )
        .then(response => {
            if(!response.ok && response.status === 401) {
                go_to_login();
            }

            return response.json();
        })
        .then(data => window.location.href=`/event/${data.response.id}`)
    }
}

function delete_event(id) {
    fetch(
        `${URLS.event}/${id}`,
        {
            "method": "delete",
            "headers": {
                "Authorization": `Bearer ${get_access_token()}`,
            }
        }
    )
    .then(response => {
        if(!response.ok && response.status === 401) {
            go_to_login();
        }

        return response.json();
    })
    .then(data => window.location.href='/organization/dashboard')
}
