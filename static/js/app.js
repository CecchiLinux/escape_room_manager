$(document).ready(function() {

  $(document).on('click', '#timer_start', function(event) {
    $.post('/event/timer_start', {}, function(data) {
      console.log('timer_stop ok');
      $("#timer_start").addClass("disabled");
      $("#timer_stop").removeClass("disabled");
    });
  });
  $(document).on('click', '#timer_stop', function(event) {
    $.post('/event/timer_stop', {}, function(data) {
      console.log('timer_stop ok');
      $("#timer_stop").addClass("disabled");
      $("#timer_start").removeClass("disabled");
    });
  });
  $(document).on('click', '#start_game', function(event) {
    $.post('/event/start_game', {}, function(data) {
      console.log('start_game ok');
      $("#timer_stop").removeClass("disabled");
      $("#start_game").addClass("disabled");
    });
  });
  $(document).on('click', '#send_text_to_room', function(event) {
    var message_text = $('#text_to_room').val();
    console.log(message_text);
    $.post('/event/text_to_room', {'text': message_text}, function(data, textStatus, xhr) {
      console.log('ok');
    });
  });
  // var x = setInterval(function() {
  //   $.post('/event/ping_broker', {}, function(data) {
  //     console.log(data);
  //   });
  // }, 5000);
});
