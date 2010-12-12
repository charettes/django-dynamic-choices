(function(context){

  var $ = context.jQuery;

  var assignOptions = $.fn.updateFields.widgetHandlers['default'];

  var filteredSelectMultiple = 'django.contrib.admin.widgets.FilteredSelectMultiple';
  $.fn.updateFields.widgetHandlers[filteredSelectMultiple] = function(field, values) {
    var chosenField = $(field),
        alreadyChosens = $(field.options).map(function(index, element){
          return element.value;
        }),
        availableField = $('#id_' + field.name + '_from'),
        fromCache = [],
        toCache = [],
        availables = [], chosens = [];

    SelectBox.cache['id_' + field.name + '_from'] = [];
    SelectBox.cache['id_' + field.name + '_to'] = [];

    availableField.empty();
    chosenField.empty();
    
    $(values).each(function(index, value){
      //We cast the value to string since the "type" is lost when retreiving
      //from option.value by SelectBox
      var chosen = $.inArray(String(value[0]), alreadyChosens) != -1; 
      (chosen ? chosens : availables).push(value);
      (chosen ? toCache : fromCache).push({value: value[0], text: value[1], displayed: 1});
    });
    
    SelectBox.cache['id_' + field.name + '_from'] = fromCache;
    SelectBox.cache['id_' + field.name + '_to'] = toCache;
    
    assignOptions(availableField, availables);
    assignOptions(chosenField, chosens);
  };

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
