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

function go_to_event(id) {
    window.location.href=`/event/${id}`;
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
    if(saved_by <= 100) return saved_by;
    else if(saved_by > 100 && saved_by <= 999) return "100+";
    else if (saved_by > 1_000 && saved_by <= 9_999) return "1k+";
    else if(saved_by > 10_000 && saved_by <= 99_999) return "10k+";
    else if (saved_by > 100_000 && saved_by <= 999_999) return "100k+";

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
        const interested_in_container = $('div#interested_in_container');
        const card_id = $(this).attr('id');

        interested_in_container.each(function(){
            $(this).append(
                `<input type="hidden" name="interested_in" value="${card_id}">`
            )
        });
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

function call_rest_countries(city) {
    return fetch(
        `${URLS.rest_countries}/capital/${encodeURIComponent(city)}?fields=capital,name,capitalInfo`
    ).then(response => {
        if(!response.ok) {
            throw new Error("error while retrieving capital");
        }

        return response.json();
    })
}

function search_for_capital(city, autocomplete_element, element_id) {
    if(!city) throw new Error("city is null!");
    call_rest_countries(city)
        .then(data => {
            $(`#${autocomplete_element}`).empty();
            data.forEach(element => {
                $(`#${autocomplete_element}`).append(`
                    <div onclick="set_city('${autocomplete_element}', '${element_id}', '${element.capital[0]}', '${element.capitalInfo.latlng}')" class="ps-3 px-1 autocomplete-item">${element.name.common}, ${element.capital[0]}</div>
                `);

                $(`#${autocomplete_element}`).css("display", "");
            });
            $(`#${autocomplete_element}`).css("z-index", "999");
        });
}

function set_city(autocomplete_element, element_id, city, coordinates) {
    if(city) {
        $(`#${element_id}`).val(city);
        $(`#${autocomplete_element}`).empty();
        if($("#city_lat").length) $("#city_lat").val(coordinates.split(',')[0]);
        if($("#city_lng").length) $("#city_lng").val(coordinates.split(',')[1]);
    }
}

function generate_itinerary(event_id) {
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
            `${URLS.itinerary}/request${ event_id ? `/event/${event_id}` : ''}`,
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
        if(data.response.status === "PENDING") {
            setTimeout(() => get_itinerary_request(id, map), 1000);
            window.scrollTo(0, document.body.scrollHeight);
        } else {
            $("#actions_container").empty();
            $("#actions_container").append(`
            <a id="save_itinerary" href="#" data-bs-placement="bottom" data-bs-toggle="tooltip" data-bs-title="Save itinerary"><img class="img-fluid" src="../../static/svg/save-itinerary.svg" alt="save"></a>
            `);
            $("#save_itinerary").on("click", () => create_itinerary(`${data.response.id}`));
            $("#details-container-placeholder").remove();
            $("#itinerary_date").text(moment(data.response.start_date).format("D MMM YYYY") + "-" + moment(data.response.end_date).format("D MMM YYYY"))
            window.scrollTo(0, 0);
        }

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
            const owner_components = itinerary.is_owner
                ? `<div class="d-none d-2xl-block">
                      <div class="d-flex justify-content-between mt-3">
                            <div class="pt-2">
                                <span><img src="${itinerary.is_public ? "../../static/svg/published.svg": "../../static/svg/publish.svg"}" alt="publish" id="img_publish" onclick="publish_itinerary('${itinerary.id}', 'itinerary${num}')" style="cursor: pointer"></span>
                                <span class="ms-3"><img src="../../static/svg/trash.svg" alt="trash" onclick="delete_itinerary('${itinerary.id}')" style="cursor: pointer"></span>
                            </div>
                            <input type="hidden" id="is_public" value="${itinerary.is_public ? "true" : ""}">
                          <button id="invite_traveler_btn${num}" data-bs-toggle="modal" data-bs-target="#inviteTravelersModal" data-itinerary-id="${itinerary.id}" class="px-5 py-1 fs-20 rounded bg-secondary border-0 fw-medium">Invite travelers</button>
                      </div>
                  </div>
                  <div class="d-none d-md-block d-2xl-none">
                      <div class="d-flex justify-content-between mt-2 mt-xl-4 mt-xxl-4">
                          <div class="pt-2">
                              <span><img src="${itinerary.is_public ? "../../static/svg/published.svg": "../../static/svg/publish.svg"}" alt="publish" id="img_publish" onclick="publish_itinerary('${itinerary.id}', 'itinerary${num}')" style="cursor: pointer"></span>
                          </div>
                          <input type="hidden" id="is_public" value="${itinerary.is_public ? "true" : ""}">
                          <button id="invite_traveler_btn${num}" data-bs-toggle="modal" data-bs-target="#inviteTravelersModal" data-itinerary-id="${itinerary.id}" class="d-none d-xxl-block px-5 py-1 fs-20 rounded bg-secondary border-0 fw-medium">Invite travelers</button>
                          <button id="invite_traveler_btn${num}" data-bs-toggle="modal" data-bs-target="#inviteTravelersModal" data-itinerary-id="${itinerary.id}" class="d-none d-xl-block d-xxl-none px-5 py-1 fs-18 rounded bg-secondary border-0 fw-medium">Invite travelers</button>
                          <button id="invite_traveler_btn${num}" data-bs-toggle="modal" data-bs-target="#inviteTravelersModal" data-itinerary-id="${itinerary.id}" class="d-none d-lg-block d-xl-none px-5 py-1 fs-16 rounded bg-secondary border-0 fw-medium">Invite travelers</button>
                          <button id="invite_traveler_btn${num}" data-bs-toggle="modal" data-bs-target="#inviteTravelersModal" data-itinerary-id="${itinerary.id}" class="d-block d-lg-none px-5 py-1 fs-14 rounded bg-secondary border-0 fw-medium">Invite travelers</button>
                      </div>
                  </div>
                  <div class="d-block d-md-none">
                      <div class="d-flex justify-content-between mt-3">
                          <div class="pt-2">
                            <span><img src="${itinerary.is_public ? "../../static/svg/published.svg": "../../static/svg/publish.svg"}" alt="publish" id="img_publish" onclick="publish_itinerary('${itinerary.id}', 'itinerary${num}')" style="cursor: pointer"></span>
                          </div>
                          <input type="hidden" id="is_public" value="${itinerary.is_public ? "true" : ""}">
                          <button id="invite_traveler_btn${num}" data-bs-toggle="modal" data-bs-target="#inviteTravelersModal" data-itinerary-id="${itinerary.id}" class="px-5 py-1 fs-14 rounded bg-secondary border-0 fw-medium">Invite travelers</button>
                      </div>
                  </div>`
                : "";
            $("#upcoming_container").append(`
            <div class="col-12 px-md-5">
                <div id="itinerary${num}" class="card border-0 shadow mb-3 w-full">
                    <div class="row g-0">
                        <div class="col-12 col-sm-6">
                          <div class="card-body">
                              <div class="row align-items-center">
                                  <div class="col">
                                      <h5 class="d-none d-xxl-block card-title m-0 fs-36 fw-bold">${itinerary.country}, ${itinerary.city}</h5>
                                      <h5 class="d-none d-xl-block d-xxl-none card-title m-0 fs-28 fw-bold">${itinerary.country}, ${itinerary.city}</h5>
                                      <h5 class="d-none d-md-block d-xl-none card-title m-0 fs-24 fw-bold">${itinerary.country}, ${itinerary.city}</h5>
                                      <h5 class="d-block d-md-none card-title m-0 fs-20 fw-bold">${itinerary.country}, ${itinerary.city}</h5>
                                  </div>
                                  <div class="d-none d-lg-block col">
                                      <div class="d-flex justify-content-end">
                                          <span class="d-none d-xxl-block badge text-bg-dark lh-lg px-3 fs-14">${itinerary.days_from_start <= 0 ? "Ongoing" : `In ${itinerary.days_from_start} day${itinerary.days_from_start === 0 || itinerary.days_from_start > 1 ? "s" : ""}`}</span>
                                          <span class="d-none d-lg-block d-xxl-none badge text-bg-dark lh-lg px-3 fs-12">${itinerary.days_from_start <= 0 ? "Ongoing" : `In ${itinerary.days_from_start} day${itinerary.days_from_start === 0 || itinerary.days_from_start > 1 ? "s" : ""}`}</span>
                                      </div>
                                  </div>
                                  <div class="d-block d-lg-none col-2">
                                        <div class="d-flex justify-content-end">
                                           <span class="ms-2"><img src="../../static/svg/trash.svg" alt="trash" onclick="delete_itinerary('${itinerary.id}')" style="cursor: pointer"></span>
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
                              ${owner_components}
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

            $(`button#invite_traveler_btn${num}`).each(function () {
                $(this).on('click', () => {
                    const itinerary_id = $(this).data('itinerary-id');
                    $("#inviteTravelersModal #itinerary_id").val(itinerary_id);
                    get_shared_with(itinerary_id);
                });
            })
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

function delete_itinerary(id) {
    fetch(
        `${URLS.itinerary}/${id}`,
        {
            "method": "delete",
            "headers": {
                "Authorization": `Bearer ${get_access_token()}`,
                "Content-Type": "application/json"
            },
            "body": JSON.stringify({
                "id": id
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
        $("#upcoming_container").empty();
        get_upcoming_itineraries()
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

    const interested_in = [];
    $("input#interested_in").each(function () { interested_in.push($(this).val()) });

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
                "interested_in": interested_in,
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
    const latitude = $("#latitude").val();
    const longitude = $("#longitude").val();

    let interested_in = []
    $("input[name='interested-in']:checked").each(function () {
      interested_in.push($(this).attr("value"));
    })

    if(!title) {
        show_error_toast("Title required!")
        return false;
    }

    if(!city) {
        show_error_toast("City required!")
        return false;
    }

    if(!start_date || !end_date) {
        show_error_toast("Start date and end date must not be empty!");
        return false;
    } else {
        $('#start_date').attr("value", start_date.format('YYYY-MM-DD'));
        $('#end_date').attr("value", end_date.format('YYYY-MM-DD'));
    }

    if(!latitude) {
        show_error_toast("Latitude required!");
        return false;
    }

    if(!longitude) {
        show_error_toast("Longitude required!");
        return false;
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
        const latitude = $("#latitude").val();
        const longitude = $("#longitude").val();

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
                    "end_date": end_date,
                    "coordinates": {
                        "lat": latitude,
                        "lng": longitude
                    }
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
        const latitude = $("#latitude").val();
        const longitude = $("#longitude").val();

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
                    "end_date": end_date,
                    "coordinates": {
                        "lat": latitude,
                        "lng": longitude
                    }
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

function update_organization() {
    const organization_name = $("#organization_name").val();
    const old_organization_name = $("#organization_name").data("defaultValue");
    const email = $("#email").val();
    const old_email = $("#email").data("defaultValue");
    const phone_number = $("#phone_number").val();
    const old_phone_number = $("#phone_number").data("defaultValue");
    const website = $("#website").val();
    const old_website = $("#website").data("defaultValue");

    if(!organization_name || !email || !validate_email(email) || !phone_number || !website) {
        show_error_toast("Cannot update, all data are required!");
        return;
    }

    if(
        organization_name === old_organization_name &&
        email === old_email &&
        phone_number === old_phone_number &&
        website === old_website
    ) {
        show_success_toast("No data to update!");
        return;
    }

    fetch(
        `${URLS.organization}`,
        {
            "method": "put",
            "headers": {
                "Authorization": `Bearer ${get_access_token()}`,
                "Content-Type": "application/json"
            },
            "body": JSON.stringify({
                "email": email,
                "organization_name": organization_name,
                "phone_number": phone_number,
                "website": website,
                "coordinates": { "lat": "51.505", "lng": "-0.09"}
            })
        }
    )
    .then(response => {
        if(!response.ok && response.status === 401) {
            go_to_login();
        }

        $("#organization_name").data("defaultValue", organization_name);
        $("#email").data("defaultValue", email);
        $("#phone_number").data("defaultValue", phone_number);
        $("#website").data("defaultValue", website);

        show_success_toast("Successfully updated organization!");
    })
}

function validate_organization_signup() {
    const email = $("#email").val();
    const organization_name = $("#organization_name").val();
    const password = $("#password").val();
    const confirm_password = $("#confirm_password").val();

    const is_email_valid = validate_email(email);
    const is_organization_name_valid = organization_name && organization_name.length > 0;
    const is_password_valid = validate_password(password, confirm_password)

    if(!is_email_valid) show_error_toast("Email has not a valid format!");
    if(!is_organization_name_valid) show_error_toast("Organization name is required!");
    if(!is_password_valid) show_error_toast("Passwords do not match!");

    return is_email_valid && is_organization_name_valid && is_password_valid;
}

function find_travelers_by_email(email) {
    if(!email) {
        throw new Error('email format not correct!')
    }

    fetch(
        `${URLS.user}/search`,
        {
            "method": "POST",
            "headers": {
                "Authorization": `Bearer ${get_access_token()}`,
                "Content-Type": "application/json"
            },
            "body": JSON.stringify({
                "role": "TRAVELER",
                "email": email,
            })
        }
    )
    .then(response => {
        if(!response.ok && response.status === 401) {
            throw new Error("Authentication error!")
        }

        return response.json();
    })
    .then(data => {
        $("#travelers_autocomplete").empty();

        data.response.forEach(user => {
            $("#travelers_autocomplete").append(`
            <span onclick="set_user_id('${user.id}', 'email_search')">${user.email}</span>
            `)
        })
    })
}

function set_user_id(id, element_id) {
    $(`#${element_id}`).val(id);
}

function share_itinerary(itinerary_id, email) {
    if(!itinerary_id || !email || !validate_email(email)) throw new Error('invalid params!');

    fetch(
        `${URLS.itinerary}/share-with`,
        {
            "method": "post",
            "headers": {
                "Authorization": `Bearer ${get_access_token()}`,
                "Content-Type": "application/json"
            },
            "body": JSON.stringify({
                "id": itinerary_id,
                "users": [email]
            })
        }
    )
    .then(response => {
        if(!response.ok && response.status === 401) {
            throw new Error("Authentication error!");
        }

        get_shared_with(itinerary_id)
        $("#traveler_email").val("")
    })
}

function get_shared_with(itinerary_id) {
    if(!itinerary_id) {
        throw new Error("invalid itinerary id!");
    }

    fetch(
        `${URLS.itinerary}/shared-with/${itinerary_id}`,
        {
            "headers": {
                "Authorization": `Bearer ${get_access_token()}`,
            }
        }
    )
    .then(response => {
        if(!response.ok && response.status === 401) {
            throw new Error("Authentication error!");
        }

        return response.json();
    })
    .then(data => {
        data.response.shared_with.forEach(user => {
            $("#shared_with_container").append(`
            <span class="bg-white border border-1 border-black rounded-pill px-3 py-1 d-inline-block">
                ${user.email}<a href="#" class="ms-3 mb-2 my-auto"><img src="../../../static/svg/cross.svg"alt="close" onclick="remove_shared_with('${itinerary_id}', '${user.id}')"></a>
            </span>
            `)
        })
    })
}

function remove_shared_with(itinerary_id, user_id) {
    if(!itinerary_id || !user_id) throw new Error('invalid params!');

    fetch(
        `${URLS.itinerary}/remove/shared-with`,
        {
            "method": "post",
            "headers": {
                "Authorization": `Bearer ${get_access_token()}`,
                "Content-Type": "application/json"
            },
            "body": JSON.stringify({
                "id": itinerary_id,
                "users": [user_id]
            })
        }
    )
    .then(response => {
        if(!response.ok && response.status === 401) {
            throw new Error("Authentication error!");
        }

        $("#shared_with_container").empty();
        get_shared_with(itinerary_id);
    })
}

function duplicate_itinerary(itinerary_id) {
    if(!itinerary_id) throw new Error("invalid itinerary id!");

    const start_date = $("#start_date").val();
    if(!start_date) throw new Error("invalid start_date!");

    fetch(
        `${URLS.itinerary}/duplicate`,
        {
            "method": "post",
            "headers": {
                "Authorization": `Bearer ${get_access_token()}`,
                "Content-Type": "application/json"
            },
            "body": JSON.stringify({
                "id": itinerary_id,
                "start_date": start_date
            })
        }
    )
    .then(response => {
        if(!response.ok && response.status === 401) {
            throw new Error("Authentication error!");
        }

        return response.json();
    })
    .then(data => go_to_itinerary(data.response.id))
}

function get_upcoming_events() {
    fetch(
        `${URLS.event}/upcoming`,
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
            throw new Error("Authentication error!");
        }

        return response.json();
    })
    .then(data => {
        data.response.content.forEach(event => {
            $("#upcoming_events_2xl").append(`
            <div class="col-12">
                <div class="d-flex justify-content-between px-3" onclick="go_to_event('${event.id}')" style="cursor: pointer">
                    <span class="text-muted">${moment(event.start_date).format("D MMM YYYY")} - ${moment(event.end_date).format("D MMM YYYY")}</span>
                    <span class="fw-medium">${event.title}</span>
                </div>
                <hr>
            </div>
            `);
            $("#upcoming_events_xxl").append(`
            <div class="col-12">
                <div class="d-flex justify-content-between px-3" onclick="go_to_event('${event.id}')" style="cursor: pointer">
                    <span class="text-muted">${moment(event.start_date).format("D MMM YYYY")} - ${moment(event.end_date).format("D MMM YYYY")}</span>
                    <span class="fw-medium">${event.title}</span>
                </div>
                <hr>
            </div>
            `);
            $("#upcoming_events_xl").append(`
            <div class="col-12">
                <div class="d-flex justify-content-between px-3" onclick="go_to_event('${event.id}')" style="cursor: pointer">
                    <span class="text-muted">${moment(event.start_date).format("D MMM YYYY")} - ${moment(event.end_date).format("D MMM YYYY")}</span>
                    <span class="fw-medium">${event.title}</span>
                </div>
                <hr>
            </div>
            `);
            $("#upcoming_events_lg").append(`
            <div class="col-12">
                <div class="d-flex justify-content-between px-3" onclick="go_to_event('${event.id}')" style="cursor: pointer">
                    <span class="text-muted fs-14">${moment(event.start_date).format("D MMM YYYY")} - <br>${moment(event.end_date).format("D MMM YYYY")}</span>
                    <span class="fw-medium fs-14">${event.title}</span>
                </div>
                <hr>
            </div>
            `);
            $("#upcoming_events_md").append(`
            <div class="col-12">
                <div class="d-flex justify-content-between px-3" onclick="go_to_event('${event.id}')" style="cursor: pointer">
                    <span class="text-muted fs-14">${moment(event.start_date).format("D MMM YYYY")} - <br>${moment(event.end_date).format("D MMM YYYY")}</span>
                    <span class="fw-medium fs-14">${event.title}</span>
                </div>
                <hr>
            </div>
            `);
            $("#upcoming_events").append(`
            <div class="col-12">
                <div class="d-flex justify-content-between px-3" onclick="go_to_event('${event.id}')" style="cursor: pointer">
                    <span class="text-muted fs-12">${moment(event.start_date).format("D MMM YYYY")} - <br>${moment(event.end_date).format("D MMM YYYY")}</span>
                    <span class="fw-medium fs-12">${event.title}</span>
                </div>
                <hr>
            </div>
            `);
        })
    })
}

function get_other_events() {
    return fetch(
        `${URLS.event}/other`,
        {
            "headers": {
                "Authorization": `Bearer ${get_access_token()}`
            }
        }
    )
    .then(response => {
        if(!response.ok && response.status === 401) {
            throw new Error("Authentication error!");
        }

        return response.json();
    })
    .then(data => {
        const carousel_events_img = [
            "https://images.unsplash.com/photo-1536663815808-535e2280d2c2?q=80&w=1964&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
            "https://plus.unsplash.com/premium_photo-1697730214411-90916c40f30d?q=80&w=1935&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
            "https://images.unsplash.com/photo-1511527661048-7fe73d85e9a4?q=80&w=1965&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
            "https://plus.unsplash.com/premium_photo-1675975706513-9daba0ec12a8?q=80&w=2070&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
            "https://images.unsplash.com/photo-1448906654166-444d494666b3?q=80&w=2070&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
        ]
        data.response.forEach((event, event_num) => {
            event.related_activities.forEach(activity => {

                $("#event_carousel_container").append(`
            <div id="event_carousel_${event_num}" class="carousel-item ${event_num === 0 ? "active" : ""} pb-1" data-title="${event.title}" onclick="go_to_event('${event.id}')" style="cursor:pointer;">
                <div class="row">
                    <div class="col">
                        <img class="d-none d-2xl-block object-fit-cover w-100" height="250" alt="event_img" src="${carousel_events_img[event_num]}">
                        <img class="d-none d-xxl-block d-2xl-none object-fit-cover w-100" height="200" alt="event_img" src="${carousel_events_img[event_num]}">
                        <img class="d-none d-xl-block d-xxl-none object-fit-cover w-100" height="180" alt="event_img" src="${carousel_events_img[event_num]}">
                        <img class="d-block d-xl-none object-fit-cover w-100" height="140" alt="event_img" src="${carousel_events_img[event_num]}">
                    </div>
                </div>
                <div class="row mt-2">
                    <div class="col">
                        <h1 class="fs-32 fw-medium m-0">${event.title}</h1>
                        <span class="text-muted fw-thin">${moment(event.start_date).format("D MMM YYYY")} - ${moment(event.end_date).format("D MMM YYYY")}</span>
                    </div>
                </div>
                <div class="row mt-3">
                    <div class="col" id="event_related_activities_${event_num}"></div>
                </div>
            </div>
            `)
                $(`#event_related_activities_${event_num}`).append(`
                <span class="bg-white border border-1 border-black rounded-pill px-2 py-1 d-inline-block mb-1 fs-14">${decode_interested_in(activity)}</span>
                `)
            })
        })
    })
}

function get_past_events() {
    fetch(
        `${URLS.event}/past`,
        {
            "headers": {
                "Authorization": `Bearer ${get_access_token()}`
            }
        }
    )
    .then(response => {
        if(!response.ok && response.status === 401) {
            throw new Error("Authentication error!");
        }

        return response.json();
    })
    .then(data => {
        const past_events_img = [
            "https://images.unsplash.com/photo-1522093007474-d86e9bf7ba6f?q=80&w=1600&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
            "https://plus.unsplash.com/premium_photo-1661887237533-b38811c27add?q=80&w=2070&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
            "https://images.unsplash.com/photo-1513326738677-b964603b136d?q=80&w=1949&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
            "https://images.unsplash.com/photo-1510154328089-bdd27fc4ff66?q=80&w=1974&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
            "https://images.unsplash.com/photo-1448317971280-6c74e016e49c?q=80&w=2132&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
        ]
        data.response.forEach((event, event_num) => {
            $("#recent_events_container").append(`
            <div class="col-12 col-md-6 col-lg-4 col-xl-3 col-xxl-2">
                <div class="card border border-0 rounded-0 w-100" role="button" onclick="go_to_event('${event.id}')">
                  <img class="card-img-top rounded-0 w-100 object-fit-cover" height="381" src="${past_events_img[event_num]}" alt="event_img">
                  <div class="card-body px-1 py-2 rounded-0">
                    <h5 class="card-title fw-bold fs-24">${event.title}</h5>
                    <p class="text-muted fs-14">${moment(event.start_date).format("D MMM YYYY")} - ${moment(event.start_date).format("D MMM YYYY")}</p>
                    <div class="d-flex justify-content-between mt-2">
                        <div>
                            <img src="../../../static/svg/clock.svg" alt="clock_img" class="me-2">
                            <span class="fs-14">${event.avg_duration}min</span>
                        </div>
                        <div>
                            <img src="../../../static/svg/money.svg" alt="money_img" class="me-2">
                            <span class="fs-14">${event.cost}</span>
                        </div>
                    </div>
                  </div>
                </div>
            </div>
            `)
        })
    })
}

function get_events_stats() {
    fetch(
        `${URLS.event}/stats`,
        {
            "headers": {
                "Authorization": `Bearer ${get_access_token()}`
            }
        }
    )
    .then(response => {
        if(!response.ok && response.status === 401) {
            throw new Error("Authentication error!");
        }

        return response.json();
    })
    .then(data => {
        $("span#live_events").each(function() {
            $(this).text(data.response.active_events);
        })
        $("span#most_chosen_city").each(function() {
            $(this).text(data.response.most_used_city);
        })
        $("span#last_event_created_at").each(function() {
            $(this).text(moment(data.response.last_event_created_at).format("D MMM YYYY"));
        })
        $("span#events_created").each(function() {
            $(this).text(data.response.events_created);
        })
    })
}

function get_event_by_id(event_id) {
    if(!event_id) throw new Error("invalid event id!");
    return fetch(
        `${URLS.event}/itinerary/${event_id}`,
        {
            "headers": {
                "Authorization": `Bearer ${get_access_token()}`
            }
        }
    )
    .then(response => {
        if(!response.ok && response.status === 401) {
            throw new Error("Authentication error!");
        }

        return response.json();
    });
}