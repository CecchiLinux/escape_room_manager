$(document).ready(function() {

  $(document).on('click', '#send_text_to_room', function(event) {
    var message_text = $('#text_to_room').val();
    console.log(message_text);
    $.post('/event/text_to_room', {'text': message_text}, function(data, textStatus, xhr) {
      console.log('ok');
    });
  });
});
