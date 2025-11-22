document.addEventListener("DOMContentLoaded", function () {
  const sliders = document.querySelectorAll('.myAdsSwiper');

  sliders.forEach(slider => {
    new Swiper(slider, {
      loop: true,
      speed: 600,
      autoplay: {
        delay: 3000,
        disableOnInteraction: false,
      },
      pagination: {
        el: slider.querySelector('.swiper-pagination'),
        clickable: true,
      },
      navigation: {
        nextEl: slider.querySelector('.swiper-button-next'),
        prevEl: slider.querySelector('.swiper-button-prev'),
      },
    });
  });
});
