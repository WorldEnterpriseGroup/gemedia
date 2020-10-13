/*

Titan Slider JS
Version 3.0
Made by Themanoid

*/

;(function($) {

  $.fn.titanSlider = function( options ) {

    var slider          = this,
        slides          = slider.find('.slides'),
        slide           = slider.find('.slide'),
        sliderWidth     = slider.width(),
        slidesWidth     = slides.width(),
        len             = parseInt(slide.length),
        current         = 1,
        index           = 1,
        first           = slide.filter(':first'),
        last            = slide.filter(':last'),
        mousePos        = { x: -1, y: 0 },
        thumbContainer  = $('<ul class="titanThumbContainer"></ul>'),
        autoplay        = null,
        autoplayActive  = false,
        isLink          = null,
        settings        = $.extend({
                        // These are the defaults.
                        carousel: false,
                        autoplay: false,
                        autoplaySpeed: 3000
                      }, options );

    first.before(last.clone(true));
    last.after(first.clone(true));

    slider.attr('data-index', current).addClass('next');
    slide.eq(0).addClass('active');

    if(settings.carousel){

      slider.after(thumbContainer);
      slider.addClass('titanCarousel');
      var thumbCount = 1;
      slide.each(function(){
        var img = slide.eq(thumbCount-1).find('img').clone();
        var li = $('<li data-thumb="'+thumbCount+'"></li>');
        li.append(img);
        $('.titanThumbContainer').append(li);
        thumbCount++;
      });

      $('.titanThumbContainer li').eq(0).addClass('active');

      $('body').on('click', '.titanThumbContainer li', function(){
        $(this).addClass('active').siblings().removeClass('active');
        var toSlide = parseInt($(this).attr('data-thumb'));
        slide.filter('data-slide',toSlide).addClass('active').siblings().removeClass('active');
        slideJump(toSlide-1);
        clearInterval(autoplay);
        autoplayActive = false;
      });

    } else {
      TweenLite.to(slide.eq(0), 1, {scale: 1, opacity: 1, ease: Power3.easeInOut, });
      TweenLite.to(slide, 0, {scale: .8, opacity: 0, ease: Power3.easeInOut, });
    }

    if(settings.autoplay){
      autoplayActive = true;
      autoplay = setInterval(autoSlider, settings.autoplaySpeed);
    }

    slider.on('mouseout', function(){
      resetInterval();
    });

    slider.on('mouseover', function(){
      removeInterval();
    });

    thumbContainer.on('mouseout', function(){
      resetInterval();
    });

    thumbContainer.on('mouseover', function(){
      removeInterval();
    });

    function resetInterval(){
      if(!autoplayActive && settings.autoplay){
        autoplay = setInterval(autoSlider, settings.autoplaySpeed);
        autoplayActive = true;
      }
    }

    function removeInterval(){
      if(autoplayActive && settings.autoplay){
        clearInterval(autoplay);
        autoplayActive = false;
      }
    }

    function autoSlider(e){
      index++;
      slideToggle(e);
    }

    if(slide.eq(0).hasClass('dark'))
      slider.addClass('dark');

    slide.each(function(){
      $(this).attr('data-slide', index);
      index++;
    });

    slider.on('mousemove', function(e){
      setCursor(e);
    });

    function setCursor(e){
      var sOffset = slider.offset();

      mousePos.x = e.pageX - sOffset.left;
      mousePos.y = e.pageY - sOffset.top;

      if(mousePos.x > slider.width()/2)
        slider.addClass('next').removeClass('previous');
      else
        slider.addClass('previous').removeClass('next');
    }

    slider.swipe( {

      swipe:function(e, direction, distance, duration) {
        isLink = $(e.target).parent('a').length;
        if(isLink)
          return;
        if(direction == 'left')
          slider.addClass('next').removeClass('previous');
        if(direction == 'right')
          slider.addClass('previous').removeClass('next');
        slideToggle(e);
        clearInterval(autoplay);
        autoplayActive = false;
      },
      tap:function(e){
        isLink = $(e.target).parent('a').length;
        if(isLink)
          return;
        slideToggle(e);
        clearInterval(autoplay);
        autoplayActive = false;
      }

    });

    function slideJump(i){
      var curSlide = slider.find('.slide.active');
      var slideAnimation = TweenLite.to(slides, 1, {ease: Power3.easeInOut, x: -sliderWidth * i});
    }

    function slideToggle(e,auto,i){

      var cycle       = false,
          delta       = slider.hasClass('next') ? 1 : -1,
          curSlide    = null,
          curThumb    = null;

      if(auto)
        delta = 1;

      if (!TweenMax.isTweening(slides)) {

        curSlide = slide.filter('[data-slide="'+current+'"]');

        if(!settings.carousel){
          TweenLite.to(curSlide, 1, {scale: .8, opacity: 0, ease: Power3.easeInOut });
        }

        current += delta;

        slide.removeClass('active');

        cycle = !!(current === 0 || current > len);

        if (cycle) {
          current = (current === 0)? len : 1;
        }

        curSlide = slide.filter('[data-slide="'+current+'"]');
        curThumb = thumbContainer.find('[data-thumb="'+current+'"]');

        if(!settings.carousel) {
          TweenLite.to(curSlide, 1, {scale: 1, opacity: 1, ease: Power3.easeInOut });
        } else {
          curThumb.addClass('active').siblings().removeClass('active');
        }

        slider.attr('data-index', current);
        curSlide.addClass('active');
        curSlide.find('video').trigger('pause');

        if(slide.eq(current).has('video'))
          curSlide.find('video').trigger('play');

        if(curSlide.hasClass('dark'))
          slider.addClass('dark');
        else
          slider.removeClass('dark');

        if(!settings.carousel){
          setCursor(e);
        }

        var slideAnimation = TweenLite.to(slides, 1, {ease: Power3.easeInOut, x: "+=" + (-sliderWidth * delta), onComplete: function() {

          if (cycle) {
            if(delta == 1){
              TweenLite.to(slides, 0, {x: 0});
            }
            else {
              TweenLite.to(slides, 0, {x: parseInt(slidesWidth-(sliderWidth*len))});
            }
          }

        }});

      }
    }

    $(document).keydown(function(e){
      if (e.keyCode == 37 || e.keyCode == 38) { // If key is Up or Left arrow key
         slider.removeClass('next').addClass('previous');
         slideToggle(e);
         return false;
      }
      if (e.keyCode == 39 || e.keyCode == 40) { // If key is Down or Right arrow key
          slider.addClass('next').removeClass('previous');
          slideToggle(e);
          return false;
      }
    });

    $(window).on('resize', function(){
        var curIndex = parseInt(slider.find('.active').attr('data-slide'));
        sliderWidth = slider.width();
        slidesWidth = slides.width();
        TweenLite.to(slides, 0, { x: -sliderWidth * (curIndex-1) });
    });

    return this;
  }

})(jQuery);
