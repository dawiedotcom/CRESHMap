// mapserver template
{
    "name": "[name]",
    "attributes": {
	      {% for a in attributes %}
	      "{{ a }}": {
            "name": "{{ attributes[a]['name'] }}",
            "year": "{{ attributes[a]['year'] }}",
		        "value":  "[item name="{{ a }}" precision = "2"]"
        }{% if not loop.last %},{% endif %}
	      {% endfor %}
    }
}
 
