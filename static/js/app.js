$(document).ready(function() {

  $(document).on('click', '#timer_stop', function(event) {
    $.post('/event/timer_stop', {}, function(data) {
      console.log('ok');  // TODO disable stop
    });
  });
  $(document).on('click', '#timer_start', function(event) {
    $.post('/event/timer_start', {}, function(data) {
      console.log('ok');  // TODO disable start
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
