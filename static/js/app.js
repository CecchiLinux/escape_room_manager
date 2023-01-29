$(document).ready(function() {

  $(document).on('click', '#timer_start', function(event) {
    $.post('/event/timer_start', {}, function(data) {
      console.log('timer_stop ok');
      // TODO disable start
    });
  });
  $(document).on('click', '#timer_stop', function(event) {
    $.post('/event/timer_stop', {}, function(data) {
      console.log('timer_stop ok');
      // TODO disable stop
    });
  });
  $(document).on('click', '#start_game', function(event) {
    $.post('/event/start_game', {}, function(data) {
      console.log('start_game ok');
      // TODO enable stop
    });
  });
  $(document).on('click', '#send_text_to_room', function(event) {
    var message_text = $('#text_to_room').val();
    console.log(message_text);
    $.post('/event/text_to_room', {'text': message_text}, function(data, textStatus, xhr) {
      console.log('ok');
    });
  });
});
