var csrf;
var map;
var mech_id;
var query;
var prevZoomLev;
var tag;
var isAuthenticated = false;
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
            mechanicProfile(pk, "Message Sent!");
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
    var $profile = $("#profile");
    $profile.empty();
    var wrapper = $("<div>", {"id": "sendmessage", "class": "sendmessage col-xs-12"});
    $profile.append(wrapper);
    var back = $("<a>", {
        "onclick": "mechanicProfile(" + pk + ");return false",
        "href": "#",
        "class": "col-xs-12"
    }).append($("<i>", {"class": "icon-reply icon-2x"})).append(" back");
    var recipient = $("<input>", {"id": "id_recipients", "type": "hidden", "name": "recipients", "value": id});
    wrapper.append(back).append(recipient);
    var email = $("<input>", {
        "id": "id_email2",
        "type": "email",
        "name": "email",
        "class": "tabable col-xs-12",
        "tabindex": "1"
    });
    if (isAuthenticated)
        email.css('display', 'none');
    email.attr("placeholder", "Your E-mail Address");
    var emailError = $("<div>", {"class": "col-xs-12 text-danger", "id": "email_error"});
    wrapper.append(emailError).append(email);
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

function subscribe() {
    var lat = map.getCenter().lat;
    var lng = map.getCenter().lng;
    var email = $('#id_email').val();
    $.ajax({
        url: "/browse/subscribe/",
        type: "POST",
        data: {
            id_lat: lat,
            id_lng: lng,
            id_email: email,
            csrfmiddlewaretoken: csrf
        },
        success: function (data) {
            $("#sub_error").html("");
            $("#id_email").css({"border-color": "#4F8A10", "outline": "none"});
            $("#id_email").attr('readonly', 'true');
            $("#submit").html("Done!");
            $("#submit").prop("disabled", true);
        },
        error: function (xhr, errmsg, err) {
            $("#sub_error").html(xhr.responseText);
            $("#id_email").css({"border-color": "#FF0000", "outline": "none"});
        }
    });
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
    getMechanicMarkers(true);
    getMechanicNearest(center);
}

function getReviews(pk, page) {
    $.ajax({
        url: "/browse/get-reviews/",
        type: "POST",
        data: {
            id_pk: pk,
            page: page,
            csrfmiddlewaretoken: csrf
        },
        success: function (data) {
            var reviews = data.reviews;
            $("#morelink").remove();
            if ($("#reviewbody").text() == '' && reviews.length == 0)
                $("#reviews").append($("<p>", {"class": "text-center topspace30"}).text("Quite Empty Here. Be His First."));
            for (var i = 0; i < reviews.length; i++) {
                var commentWrapper = $("<blockquote>");
                var rating = $("<div>", {"class": "rating-container rating-fa pull-right", "data-content": "★★★★★"});
                rating.append($("<div>", {
                    "class": "rating-stars",
                    "data-content": "★★★★★",
                    "style": "width: " + reviews[i].rating + "%;"
                }));
                commentWrapper.append(rating);
                var comment = $("<p>", {"class": "text-left", "style": "word-wrap:break-word;"});
                comment.append($("<img>", {
                    "class": "colortext quoteicon",
                    "style": "width:50px; height:50px;",
                    "src": reviews[i].user.icon
                }));
                comment.append(reviews[i].comment);
                commentWrapper.append(comment);
                var footer = $("<footer>", {
                    "class": "bigquote text-left",
                    "style": "word-wrap:break-word;"
                }).append(reviews[i].user.name);
                commentWrapper.append(footer);
                $("#reviews").append(commentWrapper);
            }
            if (!data.last) {
                var morelink = $("<div>", {"id": "morelink", "class": "text-center", "style": "margin-bottom:15px;"});
                morelink.append($("<a>", {
                    "href": "#",
                    "onclick": "getReviews(" + pk + "," + (page + 1) + ");return false"
                }).text("Show More"));
                $("#reviews").append(morelink);
            }
        },
        error: function (xhr, errmsg, err) {
            console.log(xhr);
        }
    });
}

function mechanicProfile(pk, message) {
    var $mechanicProfile;
    var $profile = $("#profile");
    var loadingDiv = $("<div>", {"class": "text-center", "style": "margin-top:50%"});
    var loadingIcon = $("<i>", {"class": "icon-spinner icon-spin icon-5x"});
    loadingDiv.append(loadingIcon);
    $profile.empty();
    $profile.append(loadingDiv);
    $("#mmenu").data("mmenu").open();
    Object.size = function (obj) {
        var size = 0, key;
        for (key in obj) {
            if (obj.hasOwnProperty(key)) size++;
        }
        return size;
    };
    $.ajax({
        url: "/browse/get-mechanic-profile/",
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

    function jssorBlock(images) {
        var htmlBlockHead = '<br><div class="jssor_wrapper" style="min-height:0 !important">' +
            '<div id="slider1_container" style="display: none; position: relative; margin: 0 auto; width: 640px; height: 480px; overflow: hidden;">' +
            '<div u="loading" style="position: absolute; top: 0px; left: 0px;">' +
            '<div style="filter: alpha(opacity=70); opacity:0.7; position: absolute; display: block; background-color: #000; top: 0px; left: 0px;width: 100%; height:100%;"></div>' +
            '<div style="position: absolute; display: block; top: 0px; left: 0px;width: 100%;height:100%;"></div></div>' +
            '<div u="slides" style="cursor: move; position: absolute; left: 0px; top: 0px; width: 640px; height: 480px; overflow: hidden;">';
        var htmlBlockContent = '';
        for (var i = 0; i < images.length; i++) {
            var imageDiv = '<div><img u="image" src="' + images[i].thumbnail + '">';
            if (images[i].description)
                imageDiv = imageDiv + '<div class="jssor_caption"><div class="t">' + images[i].description + '</div></div>';
            imageDiv = imageDiv + '<img u="thumb" src="' + images[i].icon + '"/></div>';
            htmlBlockContent = htmlBlockContent + imageDiv;
        }
        var htmlBlockTail = '</div><div u="thumbnavigator" class="jssort03" style="left: 0; bottom: 0;">' +
            '<div style=" background-color: #000; filter:alpha(opacity=30); opacity:.3; width: 100%; height:100%;"></div>' +
            '<div u="slides" style="cursor: default;"><div u="prototype" class="p"><div class=w>' +
            '<div u="thumbnailtemplate" class="t"></div></div><div class=c></div></div></div></div></div></div>';
        return $($.parseHTML(htmlBlockHead + htmlBlockContent + htmlBlockTail));
    }

    function initJssor() {
        var options = {
            $AutoPlay: true,
            $AutoPlaySteps: 1,
            $AutoPlayInterval: 10000,
            $PauseOnHover: 1,
            $ArrowKeyNavigation: true,
            $SlideEasing: $JssorEasing$.$EaseOutQuint,
            $SlideDuration: 800,
            $MinDragOffsetToSlide: 20,
            $SlideSpacing: 0,
            $DisplayPieces: 1,
            $ParkingPosition: 0,
            $UISearchMode: 1,
            $PlayOrientation: 1,
            $DragOrientation: 1,
            $ThumbnailNavigatorOptions: {
                $Class: $JssorThumbnailNavigator$,
                $ChanceToShow: 2,
                $ActionMode: 1,
                $AutoCenter: 3,
                $Lanes: 1,
                $SpacingX: 3,
                $SpacingY: 3,
                $DisplayPieces: 9,
                $ParkingPosition: 260,
                $Orientation: 1,
                $DisableDrag: false
            }
        };
        $("#slider1_container").css("display", "block");
        var jssor_slider1 = new $JssorSlider$("slider1_container", options);

        function ScaleSlider() {
            var parentWidth = jssor_slider1.$Elmt.parentNode.clientWidth;
            if (parentWidth) {
                jssor_slider1.$ScaleWidth(parentWidth);
            }
            else
                window.setTimeout(ScaleSlider, 25);
        }

        ScaleSlider();
        $(window).bind("load", ScaleSlider);
        $(window).bind("resize", ScaleSlider);
        $(window).bind("orientationchange", ScaleSlider);
    }

    function callback(data) {
        $mechanicProfile = data;
        $profile.empty();
        if (message) {
            var alert = $("<div>", {"class": "row"});
            var alertMessage = $("<div>", {"class": "alert alert-info alert-dismissable"});
            alertMessage.append($("<a>", {"class": "panel-close close", "data-dismiss": "alert"}).append('x'));
            alertMessage.append(message);
            alert.append(alertMessage);
            $profile.append(alert);
        }
        var messageLinkWrapper = $("<div>", {"class": "col-xs-5", "style": "word-wrap:break-word;"});
        var messageLink = $("<a>", {
            "onclick": 'sendMessage("' + $mechanicProfile.id + '","' + pk + '","' + $mechanicProfile.captcha + '");return false',
            "class": "messagelink",
            "href": "#"
        });
        messageLink.append($("<i>", {"class": "icon-envelope icon-2x"}));
        messageLink.append(" Message");
        $profile.append(messageLinkWrapper.append(messageLink));
        var ratingWrapper = $("<div>", {
            "class": "col-xs-7 text-right star-rating rating-xs rating-active",
            "style": "word-wrap:break-word;"
        });
        var ratingLink = $("<a>", {"href": "#reviews"});
        var count = $("<div>", {"style": "display: inline-block;"}).append($("<h5>", {"class": "font300"}).text("(" + $mechanicProfile.ratingcount + ")"));
        var rating = $("<div>", {"class": "rating-container rating-fa", "data-content": "★★★★★"});
        rating.append($("<div>", {
            "class": "rating-stars",
            "data-content": "★★★★★",
            "style": "width: " + $mechanicProfile.rating + "%;"
        }));
        $profile.append(ratingWrapper.append(count).append(ratingLink.append(rating)));
        for (var i = 1; i < Object.size($mechanicProfile); i++) {
            $profile.append($("<div>", {
                "id": "col" + i,
                "class": "col-xs-12",
                "style": "word-wrap:break-word;"
            }));
        }
        $("#col1").append($("<div>", {
            "id": "name",
            "class": "text-center"
        }).append($("<h3>").append($mechanicProfile.name.substring(0, 50))));
        $("#col2").append($("<div>", {"id": "thumbnail", "class": "text-center"}).append($("<img>", {
            "src": $mechanicProfile.thumbnail,
            "class": "img-responsive center-block avatar-lg-resp"
        })));
        var $skills = $("<div>", {"id": "skills", "class": "topspace20 text-center"});
        for (var i = 0; i < $mechanicProfile.skills.length; i++) {
            $skills.append($("<mark>", {"class": "label label-info skills font500"}).append($mechanicProfile.skills[i]));
        }
        $("#col3").append($skills);
        $("#col4").append($("<div>", {
            "id": "bio",
            "class": "lead",
            "style": "word-wrap:break-word;"
        }).append($("<p>").append($mechanicProfile.bio)));
        var $col5 = $("#col5");
        for (var i = 0; i < $mechanicProfile.jobhistory.length; i++) {
            var job = $mechanicProfile.jobhistory[i];
            var workDiv = $("<div>", {"class": "smallbox effect2"});
            var workTitleWrapper = $("<h5>", {"class": "text-left font500"});
            var workTitleText = job.position + " - " + job.years + " year(s)";
            var workCompany = $("<h6>", {"class": "text-left font400"}).append("@ " + job.company);
            var workDescription = job.description.replace(/(?:\r\n|\r|\n)/g, '<br />');
            var work = workDiv.append(workTitleWrapper.append(workTitleText)).append(workCompany).append(workDescription);
            $col5.append(work);
        }
        if ($mechanicProfile.images.length > 0) {
            $("#col6").append(jssorBlock($mechanicProfile.images));
            initJssor();
        }
        var reviewWrapper = $("<div>", {"id": "reviews", "class": "col-xs-12"});
        reviewWrapper.append("<hr>");
        var head = $("<div>", {"class": "text-center", "style": "margin-bottom: 15px;"});
        head.append($("<h3>", {"name": "reviews", "style": "margin-bottom:0"}).text("Reviews"));
        var writeReview = $("<a>", {"href": "/browse/review/?mech_id=" + $mechanicProfile.id}).append("Write a Review");
        head.append(writeReview);
        var reviewBody = $("<div>", {"id": "reviewbody"});
        reviewWrapper.append(head).append(reviewBody);
        $profile.append(reviewWrapper);
        getReviews(pk, 1);
    }
}

//Wrapper made to push history state before calling mechanicProfile function
function mechanicProfileWrapper(pk) {
    var center = map.getCenter();
    window.history.pushState({
        'customHistory': true,
        'lat': center.lat,
        'lng': center.lng,
        'pk': pk,
        'skill': tag
    }, '', '?query=' + center.lat + ',' + center.lng + '&mech_id=' + pk + '&skill=' + tag);
    mechanicProfile(pk);
}

function getMechanicMarkers(alwaysRun) {
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
            url: "/browse/get-mechanics/",
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
                var mechanics = data;
                var _markers = L.markerClusterGroup({showCoverageOnHover: false, polygonOptions: {weight: 1}});
                for (var i = 0; i < mechanics.length; i++) {
                    var avatar_icon = L.divIcon({
                        className: 'customMarker',
                        iconSize: [50, 50],
                        popupAnchor: [0, -60],
                        html: '<img src=' + mechanics[i].icon + '></img>'
                    });
                    var popup = L.popup({autoPan: false, className: 'leaflet-popup'});
                    var marker = new L.marker(mechanics[i].latlng, {icon: avatar_icon}).bindPopup(popup);
                    marker._pk = mechanics[i].pk;
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

function getMechanicNearest(center) {
    var $boxcontainer = $("#boxcontainer");
    var loadingDiv = $("<div>", {"class": "text-center"});
    var loadingIcon = $("<i>", {"class": "icon-spinner icon-spin icon-5x"});
    loadingDiv.append(loadingIcon);
    $boxcontainer.empty();
    $boxcontainer.append(loadingDiv);
    $.ajax({
        url: "/browse/get-mechanics-nearest/",
        type: "POST",
        data: {
            id_lat: center.lat,
            id_lng: center.lng,
            id_skill: tag,
            csrfmiddlewaretoken: csrf
        },
        success: function (data) {
            var $mechanicsNearest = data;
            $boxcontainer.empty();
            if ($mechanicsNearest.length == 0 && tag) {
                $boxcontainer.append($("<h3>", {
                    "class": "font300"
                }).text("No Mechanics Found That Fit Your Criteria"));
                $boxcontainer.append($("<a>", {"href": "/posts/"}).text("Post A Request"));
            }
            else if ($mechanicsNearest.length == 0 && !tag) {
                $boxcontainer.append($("<h3>", {
                    "class": "font300",
                    "style": "color:#2ac4ea"
                }).append("Not Yet Available In This Area"));
                $boxcontainer.append($("<p>").append("Enter your email to get notified when a mechanic is available here"));
                var errorWrapper = $("<div>", {"class": "col-xs-12 text-danger", "id": "sub_error"});
                $boxcontainer.append(errorWrapper);
                var inputWrapper = $("<div>", {"class": "col-xs-12"});
                var input = $("<input>", {
                    "id": "id_email",
                    "name": "email",
                    "onkeydown": "if (event.keyCode == 13) document.getElementById('submit').click()",
                    "class": "col-xs-8 col-xs-offset-1 col-sm-6 col-sm-offset-2 col-lg-4 col-lg-offset-3"
                });
                input.attr("placeholder", "E-mail Address");
                var button = $("<button>", {
                    "type": "button",
                    "class": "btn btn-default start col-xs-2",
                    "id": "submit",
                    "style": "min-height:38px",
                    "onClick": "subscribe()"
                }).append("Submit");
                inputWrapper.append(input);
                inputWrapper.append(button);
                $boxcontainer.append(inputWrapper);
                $boxcontainer.append($("<p>").text("Or"));
                $boxcontainer.append($("<a>", {"href": "/posts/"}).text("Post A Request"));
            }
            else {
                var list = $("<ul>", {"id": "list", "class": "cbp_tmtimeline topspace20"});
                for (var i = 0; i < $mechanicsNearest.length; i++) {
                    var unit = $("<li>");
                    var miles = $("<div>", {"class": "cbp_tmtime"});
                    miles.append("<span>" + $mechanicsNearest[i].miles + " miles away</span>");
                    unit.append(miles);
                    var iconWrapper = $("<div>", {"class": "cbp_tmicon"});
                    var icon = iconWrapper.append($("<img>", {
                        "class": "img-circle",
                        "src": $mechanicsNearest[i].icon
                    }));
                    unit.append(icon);
                    var link = $("<a>", {
                        "onclick": "mechanicProfileWrapper(" + $mechanicsNearest[i].pk + ");return false",
                        "href": "#"
                    });
                    var description = $("<div>", {"class": "cbp_tmlabel"});
                    description.append('<h2 style="padding:0;">' + $mechanicsNearest[i].name.substring(0, 50) + '</h2>');
                    var ratingWrapper = $("<div>", {
                        "class": "col-xs-12 star-rating rating-xs rating-active",
                        "style": "word-wrap:break-word;"
                    });
                    var count = $("<div>", {"style": "display: inline-block;"}).append($("<h5>", {"class": "font300"}).text("(" + $mechanicsNearest[i].ratingcount + ")"));
                    var rating = $("<div>", {"class": "rating-container rating-fa", "data-content": "★★★★★"});
                    rating.append($("<div>", {
                        "class": "rating-stars",
                        "data-content": "★★★★★",
                        "style": "width: " + $mechanicsNearest[i].rating + "%;"
                    }));
                    description.append(ratingWrapper.append(count).append(rating));
                    var skills = $("<div>", {"class": "topspace20 text-center"});
                    for (var j = 0; j < $mechanicsNearest[i].skills.length; j++) {
                        skills.append($("<mark>", {"class": "label label-info skills font500"}).append($mechanicsNearest[i].skills[j]));
                    }
                    description.append(skills);
                    description.append('<p>' + $mechanicsNearest[i].bio + '</p>');
                    link.append(description);
                    unit.append(link);
                    list.append(unit);
                }
                $boxcontainer.append(list);
            }
        },
        error: function (xhr, errmsg, err) {
            console.log(xhr);
        }
    });
}

function addMapMoveEvent() {
    map.on('moveend', function (e) {
        getMechanicMarkers(false);
        getMechanicNearest(map.getCenter());
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
            getMechanicMarkers(true);
            getMechanicNearest(center);
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
        getMechanicMarkers(false);
        getMechanicNearest(center);
        if (mech_id)
            mechanicProfile(mech_id);
        history.replaceState({
            'customHistory': true,
            'lat': center.lat,
            'lng': center.lng,
            'pk': mech_id,
            'skill': tag
        }, '', '');
    }, 250);

    map.on('popupopen', function (e) {
        mechanicProfileWrapper(e.popup._source._pk);
    });
}

window.onpopstate = function (e) {
    var state = e.state;
    if (!state) return;
    if (!state.customHistory) return;
    // turn off moveend event, will launch manually later to avoid double searches
    map.off('moveend');
    override = true;
    if (state) {
        if (state.skill) {
            $("#skill_" + tag).parent().removeClass('active');
            tag = state.skill;
            $("#skill_" + tag).parent().addClass('active');
        }
        else {
            $("#skill_" + tag).parent().removeClass('active');
            tag = '';
        }
        if (state.lat)
            map.panTo([state.lat, state.lng]);
        else
            map.panTo(mapDefault);
        if (state.pk)
            mechanicProfile(state.pk);
        else
            $("#mmenu").data("mmenu").close();

    }
    else {
        $("#skill_" + tag).parent().removeClass('active');
        tag = '';
        map.panTo(mapDefault);
        $("#mmenu").data("mmenu").close();
        $("#skill_" + tag).parent().removeClass('active');
    }
    $(".collapse").collapse('hide');
    getMechanicMarkers(true);
    getMechanicNearest(map.getCenter());
    addMapMoveEvent();
    override = false;
};

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

$(function () {
    $("#mmenu").mmenu({
        navbar: {title: ""}
    }, {selectedClass: "active"});
    $("#mmenu").data('mmenu').bind('closing', function () {
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