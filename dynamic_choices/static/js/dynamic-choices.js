(function($){

  function getFieldNames(fields) {
    return fields.map(function(index, field){
      return field.name;
    }).toArray();
  };

  $.fn.updateFields = function(url, form) {
    var handlers = $.fn.updateFields.widgetHandlers;
    if (this.length) {
      form = $(form ? form : this[0].form);
      var fields = $(this).addClass('loading'),
          data = $(form).serializeArray();
      data.push({name: 'DYNAMIC_CHOICES_FIELDS',
                value:getFieldNames(fields).join(',')});
      $.getJSON(url, $.param(data), function(json){
        fields.each(function(index, field){
          if (field.name in json) {
            var data = json[field.name];
            if (data.widget in handlers) {
              handlers[data.widget](field, data.value);
            } else throw new Error('Missing handler for "' + data.widget + '" widget.');
          }
          $(field).removeClass('loading');
        });
      });
    }
    return this;
  };
  
  function assignOptions(element, options) {
    $(options).each(function(index, option) {
      $(element).append($('<option></option>').attr({value:option[0]}).html(option[1]));
    });
  };
  
  function selectWidgetHandler(select, options) {
    select = $(select);
    var value = select.val();
    select.empty();
    if ('groups' in options) {
      $(options.groups).each(function(index, group){
        var optGroup = $('<optgroup></optgroup>').attr({label:group.label});
        assignOptions(optGroup, group.options);
        select.append(optGroup);
      });
    } else assignOptions(select, options);
    select.val(value);
  };
  
  $.fn.updateFields.widgetHandlers = {
    'default': selectWidgetHandler
  };
  
  $.fn.bindFields = function(url, fields) {
    var handlers = $.fn.bindFields.widgetHandlers;
    return this.each(function(index, field){
      $(field).change(function(){
        $(fields).updateFields(url, field.form);
      });
    });
  };
  
  function defaultFieldNameExtractor(fieldset, field) {
    var match = field.match(/^([\w_]+)-(\d+)-([\w_]+)$/);
    if (match && match[1] == fieldset) {
      return {
        index: match[2],
        name: match[3]
      };
    } else throw new Error('Can\'t resolve field "' + field + '"\s of specified fieldset "' + fieldset + '".');
  };
  
  function defaultFieldSelectorBuilder(fieldset, field, index) {
    return '#id_' + fieldset + '-' + index + '-' + field;
  };
  
  function curryBuilder(fieldset, index, builder) {
    return function(index, field){
      return builder(fieldset, field, index);
    };
  };
  
  $.fn.bindFieldset = function(url, fieldset, fields, extractor, builder) {
    extractor = $.isFunction(extractor) ? extractor : defaultFieldNameExtractor;
    builder = $.isFunction(builder) ? builder : defaultFieldSelectorBuilder;
    return this.each(function(index, container){
      $(container).change(function(event){
        var target = event.target,
            field = extractor(fieldset, target.name);
        if (field.name in fields) {
          var selectors = $(fields[field.name]).map(curryBuilder(fieldset, field.index, builder));
          $(selectors.toArray().join(', ')).updateFields(url, target.form);
        }
      });
    });
  };

})(jQuery || django.jQuery);
