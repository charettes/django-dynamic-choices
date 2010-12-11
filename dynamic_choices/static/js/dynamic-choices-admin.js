(function(context){

  var $ = context.jQuery;

  context.dynamicAdmin = function(url, fields, inlines){
    $(document).ready(function(){
      for (f in fields) {
        $(f).bindFields(url, fields[f].join(', '));
      }
      for (f in inlines) {
        $('#' + f + '-group').bindFieldset(url, f, inlines[f]);
      }
    });
  };
  
})(django);
