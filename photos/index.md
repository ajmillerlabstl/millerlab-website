---
header: images/site/banner-silphium-flowers.jpg
title: Photos
nav:
  order: 8
  tooltip: Lab photos
redirect_from: /photos.html
---

{% capture content %}

{% for photo in site.data.photos %}
{% include figure.html image=photo.image caption=photo.caption %}
{% endfor %}

{% endcapture %}

{% include grid.html style="square" content=content %}
