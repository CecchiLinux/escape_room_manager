function connection_state_message(data) {
  if (data['ko']) {
    $("#connection_state").html(data['ko']);
    $("#connection_state").removeClass("ok_status");
    $("#connection_state").addClass("ko_status");
    return;
  }
  $("#connection_state").html(data['ok']);
  $("#connection_state").removeClass("ko_status");
  $("#connection_state").addClass("ok_status");
}

$(document).ready(function() {

  $(document).on('click', '#timer_start', function(event) {
    $.post('/event/timer_start', {}, function(data) {
      var res = JSON.parse(data);
      connection_state_message(res);
      if (res["ok"]) {
        console.log('timer_start ok');
        $("#timer_start").addClass("disabled");
        $("#timer_stop").removeClass("disabled");
      }
    });
  });
  $(document).on('click', '#timer_stop', function(event) {
    $.post('/event/timer_stop', {}, function(data) {
      var res = JSON.parse(data);
      connection_state_message(res);
      if (res["ok"]) {
        console.log('timer_stop ok');
        $("#timer_stop").addClass("disabled");
        $("#timer_start").removeClass("disabled");
      }
    });
  });
  $(document).on('click', '#start_game', function(event) {
    $.post('/event/start_game', {}, function(data) {
      var res = JSON.parse(data);
      connection_state_message(res);
      if (res["ok"]) {
        $("#timer_stop").removeClass("disabled");
        $("#game_success").removeClass("disabled");
        $("#start_game").addClass("disabled");
      } else {
        $("#start_game").addClass("disabled");
        $("#timer_start").removeClass("disabled");
      }
    });
  });
  $(document).on('click', '#reset_text_to_room', function(event) {
    $.post('/event/text_to_room', {'text': ""}, function(data) {
      var res = JSON.parse(data);
      connection_state_message(res);
      $('#text_to_room').val("");
    });
  });
  $(document).on('click', '#send_text_to_room', function(event) {
    var message_text = $('#text_to_room').val();
    // document.getElementById('text_alert_sound').play();
    $.post('/event/text_to_room', {'text': message_text}, function(data) {
      var res = JSON.parse(data);
      connection_state_message(res);
    });
  });
  $(document).on('click', '#test_room_connection', function(event) {
    $.post('/event/ping_room', {'text': 'test'}, function(data) {
      data = JSON.parse(data);
      connection_state_message(data);
    });
  });
  $(document).on('click', '#room_connection', function(event) {
    $.post('/event/start_room', {}, function(data) {
      data = JSON.parse(data);
      connection_state_message(data);
      if (data['ok']) {
        $(".room_ready").css("visibility", "visible");
      }
    });
  });
  // var x = setInterval(function() {
  //   $.post('/event/ping_broker', {}, function(data) {
  //     console.log(data);
  //   });
  // }, 5000);
});
