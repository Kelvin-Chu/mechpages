var csrf;
var map;
var request_id;
var query;
var prevZoomLev;
var tag;
//zoomOutLimit is set to true when the map zooms outside the set limit so that it will not display markers
var zoomOutLimit = false;
//if set to true, prevent mmenu closing event from pushing history
var override = false;
var markers = L.layerGroup();
var mapDefault = [30.269742315298256, -97.74948120117188];

function send(pk, recaptchaId) {
    $("#send").prop("disabled", true);
    $.ajax({
        url: "/browse/sendmessage/",
        type: "POST",
        data: {
            'recipients': $("#id_recipients").val(),
            'email': $("#id_email2").val(),
            'subject': $("#id_subject").val(),
            'body': $("#id_body").val(),
            'g-recaptcha-response': grecaptcha.getResponse(recaptchaId),
            'csrfmiddlewaretoken': csrf
        },
        success: function (data) {
            requestDescription(pk, "Message Sent!");
        },
        error: function (xhr, errmsg, err) {
            $("#send").prop("disabled", false);
            grecaptcha.reset(recaptchaId);
            $("#subject_error").html("");
            $("#id_subject").css({"border-color": "#e1e1e1", "outline": "none"});
            $("#body_error").html("");
            $("#id_body").css({"border-color": "#e1e1e1", "outline": "none"});
            $("#email_error").html("");
            $("#id_email2").css({"border-color": "#e1e1e1", "outline": "none"});
            $("#recaptcha_error").html("");
            if (xhr.status == '453') {
                $("#email_error").html(xhr.responseText);
                $("#id_email2").css({"border-color": "#FF0000", "outline": "none"});
                $("#id_email2").css('display', 'block');
                $("#padding").css('display', 'none');
                $("#g-recaptcha").css('display', 'block');
            }
            if (xhr.status == '451') {
                $("#subject_error").html(xhr.responseText);
                $("#id_subject").css({"border-color": "#FF0000", "outline": "none"});
            }
            if (xhr.status == '452') {
                $("#body_error").html(xhr.responseText);
                $("#id_body").css({"border-color": "#FF0000", "outline": "none"});
            }
            if (xhr.status == '454') {
                $("#recaptcha_error").html(xhr.responseText);
                $("#padding").css('display', 'none');
                $("#g-recaptcha").css('display', 'block');
            }
        }
    });
}

function sendMessage(id, pk, setcaptcha) {
    var expCallback = function () {
        grecaptcha.reset(recaptchaId);
    };
    var $request = $("#request");
    $request.empty();
    var wrapper = $("<div>", {"id": "sendmessage", "class": "sendmessage col-xs-12"});
    $request.append(wrapper);
    var back = $("<a>", {
        "onclick": "requestDescription(" + pk + ");return false",
        "href": "#",
        "class": "col-xs-12"
    }).append($("<i>", {"class": "icon-reply icon-2x"})).append(" back");
    var recipient = $("<input>", {"id": "id_recipients", "type": "hidden", "name": "recipients", "value": id});
    wrapper.append(back).append(recipient);
    var subject = $("<input>", {
        "id": "id_subject",
        "type": "text",
        "name": "subject",
        "maxlength": "120",
        "class": "tabable col-xs-12",
        "tabindex": "2"
    });
    subject.attr("placeholder", "Subject");
    var subjectError = $("<div>", {"class": "col-xs-12 text-danger", "id": "subject_error"});
    wrapper.append(subjectError).append(subject);
    var body = $("<textarea>", {
        "id": "id_body",
        "name": "body",
        "class": "tabable col-xs-12",
        "tabindex": "3"
    });
    body.attr("placeholder", "Message");
    var bodyError = $("<div>", {"class": "col-xs-12 text-danger", "id": "body_error"});
    wrapper.append(bodyError).append(body);
    var recaptcha = $("<div>", {"id": "g-recaptcha", "class": "g-recaptcha col-xs-9"});
    wrapper.append(recaptcha);
    var recaptchaId = grecaptcha.render('g-recaptcha', {
        'sitekey': '6LcXDxETAAAAALuaxvBV9bnM94gQDplSJdYvIkrl',
        'expired-callback': expCallback
    });
    var padding = $("<div>", {"id": "padding", "class": "col-xs-9", "style": "display:none"}).append(" ");
    if (setcaptcha == 'true') {
        recaptcha.css('display', 'none');
        padding.css('display', 'block');
    }
    wrapper.append(padding);
    var send = $("<button>", {
        "type": "button",
        "class": "btn btn-default start tabable col-xs-3",
        "id": "send",
        "style": "min-height:38px",
        "onClick": "send(" + pk + "," + recaptchaId + ")",
        "tabindex": "4"
    }).append("Send");
    var recaptchaError = $("<div>", {"class": "col-xs-12 text-danger", "id": "recaptcha_error"});
    wrapper.append(send).append(recaptchaError);
    var note = $("<div>", {"class": "topspace50 col-xs-12"});
    note.append($("<p>").append("Note: Your e-mail and phone number will not be shared unless it is explicitly written in your message."));
    wrapper.append(note);
}

function setSkill(skill) {
    var center = map.getCenter();
    $("#skill_" + tag).parent().removeClass('active');
    if (tag != skill) {
        tag = skill;
        window.history.pushState({
            'customHistory': true,
            'lat': center.lat,
            'lng': center.lng,
            'skill': skill
        }, '', '?query=' + center.lat + ',' + center.lng + '&skill=' + skill);
        $("#skill_" + tag).parent().addClass('active');
    }
    else {
        tag = '';
        window.history.pushState({
            'customHistory': true,
            'lat': center.lat,
            'lng': center.lng
        }, '', '?query=' + center.lat + ',' + center.lng);
    }
    $(".collapse").collapse('hide');
    getRequestMarkers(true);
    getRequestNearest(center);
}

function requestDescription(pk, message) {
    var requestData;
    var $request = $("#request");
    var loadingDiv = $("<div>", {"class": "text-center", "style": "margin-top:50%"});
    var loadingIcon = $("<i>", {"class": "icon-spinner icon-spin icon-5x"});
    loadingDiv.append(loadingIcon);
    $request.empty();
    $request.append(loadingDiv);
    $("#mmenu").data("mmenu").open();
    Object.size = function (obj) {
        var size = 0, key;
        for (key in obj) {
            if (obj.hasOwnProperty(key)) size++;
        }
        return size;
    };
    $.ajax({
        url: "/mechanics/tools/browse_requests/get-request/",
        type: "POST",
        data: {
            id_pk: pk,
            csrfmiddlewaretoken: csrf
        },
        success: function (data) {
            callback(data);
        },
        error: function (xhr, errmsg, err) {
            console.log(xhr);
        }
    });

    function callback(data) {
        requestData = data;
        $request.empty();
        if (message) {
            var alert = $("<div>", {"class": "row"});
            var alertMessage = $("<div>", {"class": "alert alert-info alert-dismissable"});
            alertMessage.append($("<a>", {"class": "panel-close close", "data-dismiss": "alert"}).append('x'));
            alertMessage.append(message);
            alert.append(alertMessage);
            $request.append(alert);
        }
        var messageLinkWrapper = $("<div>", {"class": "col-xs-5", "style": "word-wrap:break-word;"});
        var messageLink = $("<a>", {
            "onclick": 'sendMessage("' + requestData.id + '","' + pk + '","' + requestData.captcha + '");return false',
            "class": "messagelink",
            "href": "#"
        });
        messageLink.append($("<i>", {"class": "icon-envelope icon-2x"}));
        messageLink.append(" Message");
        $request.append(messageLinkWrapper.append(messageLink));
        for (var i = 1; i < Object.size(requestData); i++) {
            $request.append($("<div>", {
                "id": "col" + i,
                "class": "col-xs-12",
                "style": "word-wrap:break-word;"
            }));
        }
        $("#col1").append($("<div>", {
            "id": "name",
            "class": "text-center"
        }).append($("<h3>").append(requestData.name.substring(0, 50))));
        $("#col2").append($("<div>", {"id": "thumbnail", "class": "text-center"}).append($("<img>", {
            "src": requestData.thumbnail,
            "class": "img-responsive center-block avatar-lg-resp"
        })));
        $("#col3").append($("<div>", {
            "id": "car",
            "class": "text-center"
        }).append($("<p>").append(requestData.car)));
        $("#col4").append($("<div>", {
            "id": "skill",
            "class": "topspace20 text-center"
        }).append($("<mark>", {"class": "label label-info skills font500"}).append(requestData.skill)));
        $("#col5").append($("<div>", {
            "id": "description",
            "class": "lead",
            "style": "word-wrap:break-word;"
        }).append($("<p>").append(requestData.description)));
    }
}

//Wrapper made to push history state before calling requestDescription function
function requestDescriptionWrapper(pk) {
    var center = map.getCenter();
    window.history.pushState({
        'customHistory': true,
        'lat': center.lat,
        'lng': center.lng,
        'pk': pk,
        'skill': tag
    }, '', '?query=' + center.lat + ',' + center.lng + '&request_id=' + pk + '&skill=' + tag);
    requestDescription(pk);
}

function getRequestMarkers(alwaysRun) {
    var curZoomLev = map.getZoom();
    //certain zoom in events are excluded because events where only zoom in is done will not gain any more
    //mechanics (since the boundary is a subset of the pervious).  however, there are zoom in events that are
    //mixed with other movement so that a zoom will have a different bound (such as a map search event).  also,
    //no information is provided if the zoom is less than 7 so any zoom in event afterwards will need a query (this
    //is what zoomoutlimit is for)
    if (alwaysRun || (curZoomLev > 7 && (curZoomLev <= prevZoomLev || zoomOutLimit))) {
        var bounds = map.getBounds();
        zoomOutLimit = false;
        $.ajax({
            url: "/mechanics/tools/browse_requests/get-request-markers/",
            type: "POST",
            data: {
                id_sw_lat: bounds._southWest.lat,
                id_sw_lng: bounds._southWest.lng,
                id_ne_lat: bounds._northEast.lat,
                id_ne_lng: bounds._northEast.lng,
                id_skill: tag,
                csrfmiddlewaretoken: csrf
            },
            success: function (data) {
                var requests = data;
                var _markers = L.markerClusterGroup({showCoverageOnHover: false, polygonOptions: {weight: 1}});
                for (var i = 0; i < requests.length; i++) {
                    var avatar_icon = L.divIcon({
                        className: 'customMarker',
                        iconSize: [50, 50],
                        popupAnchor: [0, -60],
                        html: '<img src=' + requests[i].icon + '></img>'
                    });
                    var popup = L.popup({autoPan: false, className: 'leaflet-popup'});
                    var marker = new L.marker(requests[i].latlng, {icon: avatar_icon}).bindPopup(popup);
                    marker._pk = requests[i].pk;
                    _markers.addLayer(marker);
                }
                map.removeLayer(markers);
                markers = _markers;
                markers.addTo(map);
            },
            error: function (xhr, errmsg, err) {
                console.log(xhr);
            }
        });
    } else if (curZoomLev <= 7) {
        zoomOutLimit = true;
        map.removeLayer(markers);
    }
    prevZoomLev = curZoomLev;
}

function getRequestNearest(center) {
    var $boxcontainer = $("#boxcontainer");
    var loadingDiv = $("<div>", {"class": "text-center"});
    var loadingIcon = $("<i>", {"class": "icon-spinner icon-spin icon-5x"});
    loadingDiv.append(loadingIcon);
    $boxcontainer.empty();
    $boxcontainer.append(loadingDiv);
    $.ajax({
        url: "/mechanics/tools/browse_requests/get-requests-nearest/",
        type: "POST",
        data: {
            id_lat: center.lat,
            id_lng: center.lng,
            id_skill: tag,
            csrfmiddlewaretoken: csrf
        },
        success: function (data) {
            var requestsNearest = data;
            $boxcontainer.empty();
            if (requestsNearest.length == 0) {
                $boxcontainer.append($("<h3>", {
                    "class": "font300"
                }).text("No Requests Found In This Area"));
            }
            else {
                var list = $("<ul>", {"id": "list", "class": "cbp_tmtimeline topspace20"});
                $boxcontainer.append(list);
                var $list = $("#list");
                for (var i = 0; i < requestsNearest.length; i++) {
                    var unit = $("<li>");
                    var miles = $("<div>", {"class": "cbp_tmtime"});
                    miles.append("<span>" + requestsNearest[i].miles + " miles away</span>");
                    unit.append(miles);
                    var iconWrapper = $("<div>", {"class": "cbp_tmicon"});
                    var icon = iconWrapper.append($("<img>", {
                        "class": "img-circle",
                        "src": requestsNearest[i].icon
                    }));
                    unit.append(icon);
                    var link = $("<a>", {
                        "onclick": "requestDescriptionWrapper(" + requestsNearest[i].pk + ");return false",
                        "href": "#"
                    });
                    var description = $("<div>", {"class": "cbp_tmlabel"});
                    description.append('<h2 style="padding:0;">' + requestsNearest[i].name.substring(0, 50) + '</h2>');
                    var car = $("<p>", {"class": "text-center"}).text(requestsNearest[i].car);
                    description.append(car);
                    var skill = $("<div>", {"class": "topspace20 text-center"});
                    skill.append($("<mark>", {"class": "label label-info skills font500"}).append(requestsNearest[i].skill));
                    description.append(skill);
                    var descriptionText = requestsNearest[i].description;
                    if (requestsNearest[i].description.length >= 300)
                        descriptionText += " ...";
                    description.append($("<p>").text(descriptionText));
                    link.append(description);
                    unit.append(link);
                    $list.append(unit);
                }
            }
        },
        error: function (xhr, errmsg, err) {
            console.log(xhr);
        }
    });
}

function addMapMoveEvent() {
    map.on('moveend', function (e) {
        getRequestMarkers(false);
        getRequestNearest(map.getCenter());
    });
}

function initBrowse() {
    prevZoomLev = map.getZoom();
    $("#skill_" + tag).parent().addClass('active');
    new L.Control.GeoSearch({
        provider: new L.GeoSearch.Provider.Google(),
        retainZoomLevel: false,
        showMarker: false
    }).addTo(map);
    L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token={accessToken}', {
        attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a>, Imagery &copy; <a href="http://mapbox.com">Mapbox</a>, GeoSearch &copy; <a href="http://google.com">Google</a>',
        id: 'scishock.cifudpnhf1v4ctfm1won1v6qu',
        accessToken: 'pk.eyJ1Ijoic2Npc2hvY2siLCJhIjoiY2lmdWRwb3AyMXZ1aHVpa3JxZG11bGYybyJ9.ImkswjtZSzGP1e0GAuRlow'
    }).addTo(map);
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
    map.on('geosearch_foundlocations', function (e) {
        map.off('moveend');
        map.on('moveend', function (e) {
            var center = map.getCenter();
            window.history.pushState({
                'customHistory': true,
                'lat': center.lat,
                'lng': center.lng,
                'skill': tag
            }, '', '?query=' + center.lat + ',' + center.lng + '&skill=' + tag);
            getRequestMarkers(true);
            getRequestNearest(center);
        });
    });
    map.on('geosearch_showlocation', function (e) {
        map.off('moveend');
        addMapMoveEvent();
    });
    addMapMoveEvent();
    setTimeout(function () {
        //css transformation will cause the map to change size, leaflet will need to reset after (assuming 250ms)
        map.invalidateSize();
        var center = map.getCenter();
        getRequestMarkers(false);
        getRequestNearest(center);
        if (request_id)
            requestDescription(request_id);
        history.replaceState({
            'customHistory': true,
            'lat': center.lat,
            'lng': center.lng,
            'pk': request_id,
            'skill': tag
        }, '', '');
    }, 250);

    map.on('popupopen', function (e) {
        requestDescriptionWrapper(e.popup._source._pk);
    });
}

function initMap(center, lookUpError) {
    map = L.map('map', {
        center: center,
        zoom: 10,
        maxZoom: 18,
        minZoom: 3,
        dragging: false,
        touchZoom: false,
        scrollWheelZoom: false
    });
    if (map.tap) map.tap.disable();
    document.getElementById('map').style.cursor = 'default';
    if (lookUpError) {
        var note = L.DomUtil.create('h6', 'leaflet-note', map._container);
        var node = document.createTextNode('Location Not Found');
        note.appendChild(node);
        setTimeout(function () {
            var element = document.getElementsByClassName('leaflet-note');
            element[0].parentNode.removeChild(element[0]);
        }, 3000);
    }
    initBrowse();
}

window.onpopstate = function (e) {
    var state = e.state;
    var $skill = $("#skill_" + tag);
    if (!state) return;
    if (!state.customHistory) return;
    // turn off moveend event, will launch manually later to avoid double searches
    map.off('moveend');
    // important! check comment from global variable declaration
    override = true;
    if (state) {
        if (state.skill) {
            $skill.parent().removeClass('active');
            tag = state.skill;
            $skill.parent().addClass('active');
        }
        else {
            $skill.parent().removeClass('active');
            tag = '';
        }
        if (state.lat)
            map.panTo([state.lat, state.lng]);
        else
            map.panTo(mapDefault);
        if (state.pk)
            requestDescription(state.pk);
        else
            $("#mmenu").data("mmenu").close();
    }
    else {
        $skill.parent().removeClass('active');
        tag = '';
        map.panTo(mapDefault);
        $("#mmenu").data("mmenu").close();
        $skill.parent().removeClass('active');
    }
    $(".collapse").collapse('hide');
    getRequestMarkers(true);
    getRequestNearest(map.getCenter());
    addMapMoveEvent();
    override = false;
};

$(function () {
    //initialize jquery mmenu plugin
    var $mmenu = $("#mmenu");
    $mmenu.mmenu({
        navbar: {title: ""}
    }, {selectedClass: "active"});
    $mmenu.data('mmenu').bind('closing', function () {
        if (!override) {
            var center = map.getCenter();
            window.history.pushState({
                'customHistory': true,
                'lat': center.lat,
                'lng': center.lng,
                'skill': tag
            }, '', '?query=' + center.lat + ',' + center.lng + '&skill=' + tag);
        }
    });
    //make mmenu tab-able (tabable content must have the class "tabable" and tabindex)
    $(window).off($['mmenu'].keydown);
    $(window).on('keydown', function (e) {
        if ($('html').hasClass('mm-opened')) {
            if (e.keyCode == 27) {
                $("#mmenu").data("mmenu").close();
            } else if (e.keyCode == 9) {
                var lastTabIndex = 4;
                var $target = e.target;
                var curIndex = $target.tabIndex;
                if (curIndex == lastTabIndex)
                    curIndex = 0;
                var tabbables = document.querySelectorAll(".tabable");
                for (var i = 0; i < tabbables.length; i++) {
                    if (tabbables[i].tabIndex == (curIndex + 1)) {
                        tabbables[i].focus();
                        break;
                    }
                }
                e.preventDefault();
                return false;
            }
        }
    });
    //initialize map by checking if a query has been passed in through url, if so, perform geosearch, if not, mapDefault
    if (query != '') {
        new L.GeoSearch.Provider.Google().GetLocations(query, function (data) {
            if (data[0])
                initMap([data[0].Y, data[0].X], false);
            else
                initMap(mapDefault, true);
        });
    } else {
        initMap(mapDefault, false);
    }
});