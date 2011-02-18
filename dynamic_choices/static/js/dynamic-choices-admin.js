($ || jQuery || django.jQuery)(document).ready(function(){

  var $ = ($ || jQuery || django.jQuery);

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

  django.dynamicAdmin = function(fields, inlines){
  	var url = document.location.pathname + 'choices/';
    $(document).ready(function(){
      for (f in fields) {
        $(f).bindFields(url, fields[f].join(', '));
      }
      for (f in inlines) {
        $('#' + f + '-group').bindFieldset(url, f, inlines[f]);
      }
    });
  };
  
  var DATA_ORIGINAL_HREF = 'data-original-href';
  
  function getAddLink(element) {
  	var addLink = $('#add_' + element.id);
  	if (!addLink.length) throw new Error('Cannot find add link of field ' + element.id);
  	return addLink;
  };
  
  function prepareAddLink(element) {
  	var addLink = getAddLink(element);
		addLink.attr(DATA_ORIGINAL_HREF, addLink.attr('href'));
  };
  
  function updateAddLink(element, fields, fieldsetFields, parametersCallback) {
  	var addLink = getAddLink(element),
  			parameters = {},
  			encodedParameters = [];
  	
  	$(fields).each(function(index, field){
  		var name = $(field).attr('name'),
  				value = $(field).val();
  		if (value) parameters[name] = value;
  	});
  	$(fieldsetFields).each(function(index, field){
  		var name = inlineField(field).name,
  				value = $(field).val();
  		if (value) parameters[name] = value;
  	});
		
		if ($.isFunction(parametersCallback)) parameters = parametersCallback(parameters);
			
  	for (var name in parameters) {
  		encodedParameters.push([encodeURI(name), encodeURI(parameters[name])].join('='));
  	}
  	
  	$(addLink).attr('href', addLink.attr(DATA_ORIGINAL_HREF) + '?' + encodedParameters.join('&'));
  };
  
  django.dynamicAdmin.bindFieldsAddLink = function(field, fields, parametersCallback) {
  	$(field).each(function(index, element){
  		prepareAddLink(element);
  		$(fields).change(function(){
				updateAddLink(element, fields, null, parametersCallback);
			});
			updateAddLink(element, fields, null, parametersCallback);
  	});
  };
  
  function inlineField(field) {
  	var field = $(field).attr('name').split('-');
  	return {fieldset: field[0], index: field[1], name: field[2]}
  };
  
  function buildInlineFieldSelector(fieldName) {
  	return '[name$="' + fieldName + '"]';
  };
  
  function buildInlineFieldId(formsetName, fieldName, fieldIndex) {
  	return '#id_' + formsetName + '-' + fieldIndex + '-' + fieldName;
  };
  
  function buildFormsetFieldsSelector(formsetName, fields, fieldIndex) {
  	return $(fields).map(function(index, field){
  		return buildInlineFieldId(formsetName, field, fieldIndex);
  	}).toArray().join(', ');
  };
  
  django.dynamicAdmin.bindFormsetFieldsAddLink = function(formset, field, bindedFormsetFields, bindedFormFieldsSelector, parametersCallback) {
  	bindedFormsetFields = bindedFormsetFields || [];
  	bindedFormFieldsSelector = bindedFormFieldsSelector || '';
  	var fieldSelector = buildInlineFieldSelector(field);
  	$(formset).each(function(index, formset){
  		var formsetName = formset.id.match(/^(\w+)-group$/)[1]
  		bindedFieldsetFieldsSelector = $(bindedFormsetFields)
  																		.map(function(i, e){return buildInlineFieldSelector(e)})
  																		.toArray().join(', ');
  		$(formset).find(bindedFieldsetFieldsSelector).live('change', function(event){
  			var index = inlineField(event.target).index;
  			updateAddLink($(buildInlineFieldId(formsetName, field, index))[0], 
  										bindedFormFieldsSelector,
  										buildFormsetFieldsSelector(formsetName, bindedFormsetFields, index),
  										parametersCallback);
  		});
  		$(bindedFormFieldsSelector).change(function(event){
  			$(formset).find(fieldSelector).each(function(index, element){
  				var index = inlineField(element).index;
  				updateAddLink(element,
  											bindedFormFieldsSelector,
  											buildFormsetFieldsSelector(formsetName, bindedFormsetFields, index),
  											parametersCallback);
  			});
  		});
  		$(formset).find(fieldSelector).each(function(index, element){
  			prepareAddLink(element);
  			var index = inlineField(element).index;
  			updateAddLink(element,
  										bindedFormFieldsSelector,
  										buildFormsetFieldsSelector(formsetName, bindedFormsetFields, index),
  										parametersCallback);
  		});
  	});
  };
  
});
