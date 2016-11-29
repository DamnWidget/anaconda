{% if var.sublime_version < 3119 %}
    body {
        padding: 0.5em;
        {% if var.is_dark %}
            {{'.background'|css('background-color')|brightness(1.1)}}
        {% else %}
            {{'.background'|css('background-color')|brightness(0.9)}}
        {% endif %}
    }
{% else %}
    div.anaconda-tooltip {
        padding: 0.5rem;
        {% if var.is_dark %}
            {{'.background'|css('background-color')|brightness(1.1)}}
        {% else %}
            {{'.background'|css('background-color')|brightness(0.9)}}
        {% endif %}
    }
{% endif %}
