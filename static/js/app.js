$(document).ready(function() {

  $(document).on('click', '#timer_start', function(event) {
    $.post('/event/timer_start', {}, function(data) {
      var res = JSON.parse(data);
      if (res["ok"]) {
        console.log('timer_start ok');
        $("#timer_start").addClass("disabled");
        $("#timer_stop").removeClass("disabled");
      } else {
        alert("Errore: comunicazione con la stanza assente");
      }
    });
  });
  $(document).on('click', '#timer_stop', function(event) {
    $.post('/event/timer_stop', {}, function(data) {
      var res = JSON.parse(data);
      if (res["ok"]) {
        console.log('timer_stop ok');
        $("#timer_stop").addClass("disabled");
        $("#timer_start").removeClass("disabled");
      } else {
        alert("Errore: comunicazione con la stanza assente");
      }
    });
  });
  $(document).on('click', '#start_game', function(event) {
    $.post('/event/start_game', {}, function(data) {
      var res = JSON.parse(data);
      if (res["ok"]) {
        console.log('start_game ok');
        $("#timer_stop").removeClass("disabled");
        $("#start_game").addClass("disabled");
      } else {
        $("#start_game").addClass("disabled");
        $("#timer_start").removeClass("disabled");
        alert("Errore: comunicazione con la stanza assente");
      }
    });
  });
  $(document).on('click', '#reset_text_to_room', function(event) {
    $.post('/event/text_to_room', {'text': ""}, function(data) {
      console.log('ok');
      $('#text_to_room').val("");
    });
  });
  $(document).on('click', '#send_text_to_room', function(event) {
    var message_text = $('#text_to_room').val();
    document.getElementById('text_alert_sound').play();
    console.log(message_text);
    $.post('/event/text_to_room', {'text': message_text}, function(data) {
      console.log('ok');
    });
  });
  // var x = setInterval(function() {
  //   $.post('/event/ping_broker', {}, function(data) {
  //     console.log(data);
  //   });
  // }, 5000);
});
