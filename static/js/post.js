var map;
var marker;
var url;
var csrf;
var avatar_icon;
var $modal = $('#addPostModal');
var $page1 = $('#page1');
var $page2 = $('#page2');
var $page1head = $('#page1head');
var $page2head = $('#page2head');
var $cancel = $('#cancel');
var $next = $('#next');
var $prev = $('#prev');
var $submit = $('#submit');

function decimalAdjust(type, value, exp) {
    if (typeof exp === 'undefined' || +exp === 0) {
        return Math[type](value);
    }
    value = +value;
    exp = +exp;
    if (isNaN(value) || !(typeof exp === 'number' && exp % 1 === 0)) {
        return NaN;
    }
    value = value.toString().split('e');
    value = Math[type](+(value[0] + 'e' + (value[1] ? (+value[1] - exp) : -exp)));
    value = value.toString().split('e');
    return +(value[0] + 'e' + (value[1] ? (+value[1] + exp) : exp));
}

function createMarker(latlng) {
    var divIcon = L.divIcon({
        className: 'customMarker',
        iconSize: [50, 50],
        popupAnchor: [0, -60],
        html: '<img src=' + avatar_icon + '></img>'
    });
    marker = new L.marker(latlng, {icon: divIcon, draggable: true});
}

function onMapClick(e) {
    if (typeof(marker) === 'undefined' || marker == null) {
        createMarker(e.latlng);
        marker.addTo(map);
    }
    else {
        marker.setLatLng(e.latlng);
    }
}

function hidePage1() {
    $page1.css('display', 'none');
    $page1head.css('display', 'none');
    $cancel.css('display', 'none');
    $next.css('display', 'none');
}

function hidePage2() {
    $page2.css('display', 'none');
    $page2head.css('display', 'none');
    $prev.css('display', 'none');
    $submit.css('display', 'none');
}

function showPage1() {
    hidePage2();
    $page1.css('display', 'inline');
    $page1head.css('display', 'inline');
    $cancel.css('display', 'inline');
    $next.css('display', 'inline');
}

function showPage2() {
    hidePage1();
    $page2.css('display', 'inline');
    map.invalidateSize();
    $page2head.css('display', 'inline');
    $prev.css('display', 'inline');
    $submit.css('display', 'inline');
}

function error_mark(error, message, field) {
    if (typeof field !== 'undefined')
        $('#' + field).css({"border-color": "#FF0000", "outline": "none"});
    $('#' + error).html(message);
}

function error_clear(error, input) {
    if (typeof input !== 'undefined')
        $('#' + input).css({"border-color": "#e1e1e1", "outline": "none"});
    $('#' + error).html("");
}

function errors_clear() {
    error_clear("id_non_field_error");
    error_clear("id_car_make_error", "id_car_make");
    error_clear("id_car_model_error_1", "id_car_model");
    error_clear("id_car_model_error_2");
    error_clear("id_car_year_error_1", "id_car_year");
    error_clear("id_car_year_error_2");
    error_clear("id_skill_error", "id_skill");
    error_clear("id_comment_error", "id_comment");
    error_clear("id_location_error");
}

function reset_fields() {
    $("#id_car_make").val("");
    $("#id_car_model").val("");
    $("#id_car_year").val("");
    $("#id_skill").val(11);
    $("#id_comment").val("");
    $("#id_pk").val("");
}

function mark_done() {
    var pk = $("#id_item_pk").val();
    $.ajax({
        url: "/posts/mark-done/",
        type: "POST",
        data: {
            pk: pk,
            csrfmiddlewaretoken: csrf
        },
        success: function (data) {
            $('#postDoneModal').modal('hide');
            get_posts();
        },
        error: function (xhr, errmsg, err) {
            console.log(xhr);
        }
    });
}

function add_modal() {
    if (url != "/posts/") {
        reset_fields();
        url = "/posts/";
    }
    $("#id_pk").val('');
    $("#id_non_field_error").css('display', 'block');
    $('#addPostModal').modal('show');
}

function update_modal(pk) {
    url = "/posts/update-post/";
    $("#id_pk").val(pk);
    $("#id_non_field_error").css('display', 'none');
    $.ajax({
        url: url,
        type: "GET",
        data: {pk: pk},
        success: function (data) {
            $("#id_car_make").val(data.car_make);
            $("#id_car_model").val(data.car_model);
            $("#id_car_year").val(data.car_year);
            $("#id_skill").val(data.skill);
            $("#id_comment").val(data.comment);
            createMarker([data.latitude, data.longitude]);
            $('#addPostModal').modal('show');
        },
        error: function (xhr, errmsg, err) {
            console.log(xhr);
        }
    });
}

function get_posts() {
    var $head = $("<tr>").append($("<th>").text("Description"));
    $head.append($("<th>", {"style": "width:140px;"}).text("Status"));
    $head.append($("<th>", {"style": "width:75px;"}).text("Created"));
    var $content = $("#id_table_content");
    $content.empty();
    $content.append($head);
    var $loading = $('#id_loading');
    $loading.css('display', 'block');
    var $empty = $("<tr>").append($("<td>").text("You have no pending requests."));
    $empty.append($("<td>").text("N/A")).append($("<td>").text("N/A"));
    $.ajax({
        url: "/posts/get-posts/",
        type: "GET",
        success: function (data) {
            var count = 0;
            if (data.posts.length > 0) {
                $loading.css('display', 'none');
                for (var i = 0; i < data.posts.length; i++) {
                    var $row = $("<tr>", {"class": "text-left"});
                    var $comment = $("<td>");
                    var $status = $("<td>");
                    var $statusLink;
                    if (!data.posts[i].status) {
                        count += 1;
                        $comment.append($("<a>", {
                            "onClick": "update_modal(" + data.posts[i].pk + ")",
                            "href": "#"
                        }).text(data.posts[i].comment));
                        $statusLink = $("<a>", {
                            "class": "open-postDoneModal", "data-id": data.posts[i].pk, "data-toggle": "modal",
                            "data-target": "#postDoneModal", "href": "#"
                        }).text("Mark Done");
                        $status.append($("<em>").append("Pending (").append($statusLink).append(")"));
                    }
                    else {
                        $comment.append(data.posts[i].comment);
                        $status.append($("<em>").text("Completed"));
                    }
                    if (data.posts[i].comment.length >= 30)
                        $comment.append("...");
                    var $date = $("<td>").text(data.posts[i].date);
                    $row.append($comment).append($status).append($date);
                    $content.append($row);
                }
                if (count >= 5)
                    $("#id_non_field_error").text("You can only have 5 active posts. Clean up any active posts you may have.");
                else
                    $("#id_non_field_error").text("");
            }
            else {
                $loading.css('display', 'none');
                $content.append($empty);
            }
        },
        error: function (xhr, errmsg, err) {
            console.log(xhr);
        }
    });
}

function submitForm() {
    try {
        $.ajax({
            url: url,
            type: "POST",
            data: {
                pk: $("#id_pk").val(),
                latitude: decimalAdjust('round', marker.getLatLng().lat, -6),
                longitude: decimalAdjust('round', marker.getLatLng().lng, -6),
                car_make: $("#id_car_make").val(),
                car_model: $("#id_car_model").val(),
                car_year: $("#id_car_year").val(),
                skill: $("#id_skill").val(),
                comment: $("#id_comment").val(),
                csrfmiddlewaretoken: csrf
            },
            success: function (data) {
                errors_clear();
                reset_fields();
                $modal.modal('hide');
                get_posts();
            },
            error: function (xhr, errmsg, err) {
                errors_clear();
                var data = JSON.parse(xhr.responseText);
                if (data.__all__) {
                    error_mark("id_non_field_error", data.__all__[0]);
                }
                if (data.car_make)
                    error_mark("id_car_make_error", data.car_make[0], "id_car_make");
                if (data.car_model) {
                    error_mark("id_car_model_error_1", data.car_model[0], "id_car_model");
                    error_mark("id_car_model_error_2", data.car_model[0]);
                }
                if (data.car_year) {
                    error_mark("id_car_year_error_1", data.car_year[0], "id_car_year");
                    error_mark("id_car_year_error_2", data.car_year[0]);
                }
                if (data.skill)
                    error_mark("id_skill_error", data.skill[0], "id_skill");
                if (data.comment)
                    error_mark("id_comment_error", data.comment[0], "id_comment");
                if (data.longitude)
                    error_mark("id_location_error", data.longitude[0]);
                if (data.latitude)
                    error_mark("id_location_error", data.latitude[0]);
                if (data.car_make || data.car_model || data.car_year || data.skill || data.comment)
                    showPage1();
            }
        });
    }
    catch (err) {
        $("#id_location_error").text("Please mark your location.");
    }
}

$modal.on('shown.bs.modal', function () {
    showPage1();
    map = L.map('map', {
        center: [30.27, -97.75], zoom: 10, maxZoom: 18, minZoom: 3, dragging: false,
        touchZoom: false, scrollWheelZoom: false
    });
    L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token={accessToken}', {
        attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a>, Imagery &copy; <a href="http://mapbox.com">Mapbox</a>, GeoSearch &copy; <a href="http://google.com">Google</a>',
        id: 'scishock.cifudpnhf1v4ctfm1won1v6qu',
        accessToken: 'pk.eyJ1Ijoic2Npc2hvY2siLCJhIjoiY2lmdWRwb3AyMXZ1aHVpa3JxZG11bGYybyJ9.ImkswjtZSzGP1e0GAuRlow'
    }).addTo(map);
    new L.Control.GeoSearch({
        provider: new L.GeoSearch.Provider.Google(),
        retainZoomLevel: true,
        showMarker: false
    }).addTo(map);
    setTimeout(function () {
        map.invalidateSize();
    }, 250);
    L.easyButton({
        position: 'topright',
        states: [{
            stateName: 'enable-map',
            icon: 'icon-move icon-2x',
            title: 'Enable panning',
            onClick: function (btn, map) {
                map.dragging.enable();
                map.touchZoom.enable();
                map.scrollWheelZoom.enable();
                if (map.tap) map.tap.enable();
                document.getElementById('map').style.cursor = 'grab';
                btn.state('disable-map');
            }
        }, {
            stateName: 'disable-map',
            icon: 'icon-remove icon-2x',
            title: 'Disable panning',
            onClick: function (btn, map) {
                map.dragging.disable();
                map.touchZoom.disable();
                map.scrollWheelZoom.disable();
                if (map.tap) map.tap.disable();
                document.getElementById('map').style.cursor = 'default';
                btn.state('enable-map');
            }
        }]
    }).addTo(map);
    if (typeof(marker) !== 'undefined' && marker != null)
        marker.addTo(map);
    map.on('click', onMapClick);
});
$modal.on('hidden.bs.modal', function () {
    if (typeof map !== 'undefined') {
        map.remove();
        marker = null;
    }
    showPage1();
});
$(function () {
    get_posts();
});
$(document).on("click", ".open-postDoneModal", function () {
    var item_pk = $(this).data('id');
    $("#id_item_pk").val(item_pk);
});