/**
 * Motion: scroll reveal, hero parallax, card tilt.
 *
 * Three rules this file follows:
 *   1. Nothing here carries information. Remove it and the page still works.
 *   2. prefers-reduced-motion is checked first and exits before anything binds.
 *   3. Scroll and pointer work is batched into requestAnimationFrame.
 */
(function () {
	'use strict';

	var reduced = window.matchMedia( '(prefers-reduced-motion: reduce)' );

	/* Reveal targets are visible by default in CSS; JS opts them into animating. */
	function markAnimated() {
		document.documentElement.classList.add( 'has-motion' );
	}

	if ( reduced.matches ) {
		return;
	}

	markAnimated();

	/* ------------------------------------------------------------------ */
	/* Scroll reveal                                                       */
	/* ------------------------------------------------------------------ */

	var revealTargets = document.querySelectorAll( '[data-reveal]' );

	/**
	 * Reveal everything, unconditionally.
	 *
	 * Hiding content until an observer fires is only safe if the observer is
	 * guaranteed to fire. It is not: browsers suppress IntersectionObserver
	 * callbacks while a tab is hidden or backgrounded, and a page restored from
	 * the back/forward cache can miss them entirely. Without this net, a visitor
	 * could land on a blank page — so the reveal is always on a deadline.
	 *
	 * @param {NodeList|Array} nodes Elements to reveal.
	 */
	function revealAll( nodes ) {
		Array.prototype.forEach.call( nodes, function ( el ) {
			el.style.transitionDelay = '';
			el.classList.add( 'is-revealed' );
		} );
	}

	if ( revealTargets.length && 'IntersectionObserver' in window ) {
		// Failsafe: whatever has not been revealed after 2.5s gets revealed anyway.
		window.setTimeout( function () {
			revealAll( document.querySelectorAll( '[data-reveal]:not(.is-revealed)' ) );
		}, 2500 );

		var observer = new IntersectionObserver(
			function ( entries ) {
				entries.forEach( function ( entry ) {
					if ( ! entry.isIntersecting ) {
						return;
					}

					var el = entry.target;
					var siblings = el.parentNode ? Array.prototype.indexOf.call( el.parentNode.children, el ) : 0;

					// Stagger within a group, capped so long lists do not crawl.
					el.style.transitionDelay = Math.min( siblings, 5 ) * 60 + 'ms';
					el.classList.add( 'is-revealed' );

					observer.unobserve( el );
				} );
			},
			{
				rootMargin: '0px 0px -8% 0px',
				threshold: 0.08
			}
		);

		Array.prototype.forEach.call( revealTargets, function ( el ) {
			observer.observe( el );
		} );
	} else {
		revealAll( revealTargets );
	}

	/* ------------------------------------------------------------------ */
	/* Hero parallax                                                       */
	/* ------------------------------------------------------------------ */

	var scene = document.querySelector( '[data-parallax-scene]' );

	if ( scene ) {
		var layers = scene.querySelectorAll( '[data-parallax-layer]' );
		var scenePending = false;

		var applyParallax = function () {
			var rect = scene.getBoundingClientRect();

			// Skip the work entirely once the hero is off screen.
			if ( rect.bottom < 0 || rect.top > window.innerHeight ) {
				scenePending = false;
				return;
			}

			var offset = window.scrollY;

			Array.prototype.forEach.call( layers, function ( layer ) {
				var depth = parseFloat( layer.getAttribute( 'data-depth' ) ) || 0;
				layer.style.transform = 'translate3d(0,' + ( offset * depth ).toFixed( 2 ) + 'px,0)';
			} );

			scenePending = false;
		};

		var onScroll = function () {
			if ( scenePending ) {
				return;
			}
			scenePending = true;
			window.requestAnimationFrame( applyParallax );
		};

		window.addEventListener( 'scroll', onScroll, { passive: true } );
		window.addEventListener( 'resize', onScroll, { passive: true } );
		applyParallax();
	}

	/* ------------------------------------------------------------------ */
	/* Card tilt                                                           */
	/* ------------------------------------------------------------------ */

	var MAX_TILT = 5; // degrees — deliberately restrained
	var fine = window.matchMedia( '(hover: hover) and (pointer: fine)' );

	if ( fine.matches ) {
		var tiltCards = document.querySelectorAll( '[data-tilt]' );

		Array.prototype.forEach.call( tiltCards, function ( card ) {
			var pending = false;
			var nextX = 0;
			var nextY = 0;

			var render = function () {
				card.style.transform =
					'perspective(900px) rotateX(' + nextY.toFixed( 2 ) + 'deg) rotateY(' + nextX.toFixed( 2 ) + 'deg)';
				pending = false;
			};

			card.addEventListener( 'pointermove', function ( e ) {
				if ( e.pointerType !== 'mouse' ) {
					return;
				}

				var rect = card.getBoundingClientRect();
				var px = ( e.clientX - rect.left ) / rect.width - 0.5;
				var py = ( e.clientY - rect.top ) / rect.height - 0.5;

				nextX = px * MAX_TILT * 2;
				nextY = -py * MAX_TILT * 2;

				if ( ! pending ) {
					pending = true;
					window.requestAnimationFrame( render );
				}
			} );

			var reset = function () {
				card.style.transform = '';
			};

			card.addEventListener( 'pointerleave', reset );
			card.addEventListener( 'blur', reset, true );
		} );
	}

	/* ------------------------------------------------------------------ */
	/* React if the user turns reduced motion on mid-session               */
	/* ------------------------------------------------------------------ */

	var onReducedChange = function ( mq ) {
		if ( ! mq.matches ) {
			return;
		}

		document.documentElement.classList.remove( 'has-motion' );

		if ( scene ) {
			Array.prototype.forEach.call( scene.querySelectorAll( '[data-parallax-layer]' ), function ( l ) {
				l.style.transform = '';
			} );
		}

		Array.prototype.forEach.call( document.querySelectorAll( '[data-tilt]' ), function ( c ) {
			c.style.transform = '';
		} );

		Array.prototype.forEach.call( document.querySelectorAll( '[data-reveal]' ), function ( el ) {
			el.style.transitionDelay = '';
			el.classList.add( 'is-revealed' );
		} );
	};

	if ( reduced.addEventListener ) {
		reduced.addEventListener( 'change', onReducedChange );
	} else if ( reduced.addListener ) {
		reduced.addListener( onReducedChange );
	}
})();
