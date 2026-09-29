/**
 * Navigation: mobile menu, submenus, search toggle.
 *
 * Everything works with the keyboard. The mobile menu traps focus and returns
 * it to the button on close.
 */
(function () {
	'use strict';

	var FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]), select, textarea, [tabindex]:not([tabindex="-1"])';

	/* ------------------------------------------------------------------ */
	/* Mobile menu                                                         */
	/* ------------------------------------------------------------------ */

	var navToggle = document.getElementById( 'nav-toggle' );
	var nav = document.getElementById( 'primary-nav' );
	var lastFocus = null;

	function openNav() {
		lastFocus = document.activeElement;
		document.body.classList.add( 'nav-open' );
		navToggle.setAttribute( 'aria-expanded', 'true' );

		/*
		 * focus() is a no-op while the panel is still visibility:hidden, so flush
		 * the pending style change before moving focus. The rAF is a belt-and-
		 * braces retry for engines that defer the recalc past the reflow.
		 */
		void nav.offsetHeight;

		var focusFirst = function () {
			if ( nav.contains( document.activeElement ) ) {
				return;
			}
			var first = nav.querySelector( FOCUSABLE );
			if ( first ) {
				first.focus();
			}
		};

		focusFirst();
		window.requestAnimationFrame( focusFirst );
	}

	function closeNav( returnFocus ) {
		document.body.classList.remove( 'nav-open' );
		navToggle.setAttribute( 'aria-expanded', 'false' );

		if ( false === returnFocus ) {
			return;
		}

		/*
		 * Always hand focus back to the toggle. Restoring "whatever was focused
		 * before" strands the user when the menu was opened by other means.
		 */
		var target = navToggle;
		if ( lastFocus && lastFocus !== document.body && document.contains( lastFocus ) && ! nav.contains( lastFocus ) ) {
			target = lastFocus;
		}
		target.focus();
	}

	function navIsOpen() {
		return document.body.classList.contains( 'nav-open' );
	}

	if ( navToggle && nav ) {
		navToggle.addEventListener( 'click', function () {
			if ( navIsOpen() ) {
				closeNav();
			} else {
				openNav();
			}
		} );

		// Trap focus inside the open menu.
		nav.addEventListener( 'keydown', function ( e ) {
			if ( e.key !== 'Tab' || ! navIsOpen() ) {
				return;
			}

			var items = Array.prototype.filter.call(
				nav.querySelectorAll( FOCUSABLE ),
				function ( el ) {
					return el.offsetParent !== null;
				}
			);

			if ( ! items.length ) {
				return;
			}

			var first = items[ 0 ];
			var last = items[ items.length - 1 ];

			if ( e.shiftKey && document.activeElement === first ) {
				e.preventDefault();
				last.focus();
			} else if ( ! e.shiftKey && document.activeElement === last ) {
				e.preventDefault();
				first.focus();
			}
		} );

		// Close when the viewport grows back to desktop.
		// Must match the CSS breakpoint in style.css §3.
		var desktop = window.matchMedia( '(min-width: 75rem)' );
		var onChange = function ( mq ) {
			if ( mq.matches && navIsOpen() ) {
				closeNav( false );
			}
		};

		if ( desktop.addEventListener ) {
			desktop.addEventListener( 'change', onChange );
		} else if ( desktop.addListener ) {
			desktop.addListener( onChange );
		}
	}

	/* ------------------------------------------------------------------ */
	/* Submenus                                                            */
	/* ------------------------------------------------------------------ */

	var toggles = document.querySelectorAll( '.submenu-toggle' );

	Array.prototype.forEach.call( toggles, function ( btn ) {
		btn.addEventListener( 'click', function () {
			var parent = btn.closest( '.has-submenu' );
			var open = btn.getAttribute( 'aria-expanded' ) === 'true';

			// Close siblings so only one submenu is open at a time.
			Array.prototype.forEach.call( toggles, function ( other ) {
				if ( other !== btn ) {
					other.setAttribute( 'aria-expanded', 'false' );
					var p = other.closest( '.has-submenu' );
					if ( p ) {
						p.classList.remove( 'is-open' );
					}
				}
			} );

			btn.setAttribute( 'aria-expanded', open ? 'false' : 'true' );
			if ( parent ) {
				parent.classList.toggle( 'is-open', ! open );
			}
		} );
	} );

	/* ------------------------------------------------------------------ */
	/* Search                                                              */
	/* ------------------------------------------------------------------ */

	var searchToggle = document.getElementById( 'search-toggle' );
	var searchPanel = document.getElementById( 'site-search' );

	if ( searchToggle && searchPanel ) {
		searchToggle.addEventListener( 'click', function () {
			var open = searchToggle.getAttribute( 'aria-expanded' ) === 'true';

			searchToggle.setAttribute( 'aria-expanded', open ? 'false' : 'true' );
			searchPanel.hidden = open;

			if ( ! open ) {
				var field = searchPanel.querySelector( 'input[type="search"]' );
				if ( field ) {
					field.focus();
				}
			}
		} );
	}

	/* ------------------------------------------------------------------ */
	/* Escape closes whatever is open                                      */
	/* ------------------------------------------------------------------ */

	document.addEventListener( 'keydown', function ( e ) {
		if ( e.key !== 'Escape' ) {
			return;
		}

		if ( navIsOpen() ) {
			closeNav();
			return;
		}

		if ( searchToggle && searchToggle.getAttribute( 'aria-expanded' ) === 'true' ) {
			searchToggle.setAttribute( 'aria-expanded', 'false' );
			searchPanel.hidden = true;
			searchToggle.focus();
			return;
		}

		Array.prototype.forEach.call( toggles, function ( btn ) {
			if ( btn.getAttribute( 'aria-expanded' ) === 'true' ) {
				btn.setAttribute( 'aria-expanded', 'false' );
				var p = btn.closest( '.has-submenu' );
				if ( p ) {
					p.classList.remove( 'is-open' );
				}
			}
		} );
	} );

	/* Close open submenus when clicking away. */
	document.addEventListener( 'click', function ( e ) {
		if ( e.target.closest( '.has-submenu' ) ) {
			return;
		}

		Array.prototype.forEach.call( toggles, function ( btn ) {
			btn.setAttribute( 'aria-expanded', 'false' );
			var p = btn.closest( '.has-submenu' );
			if ( p ) {
				p.classList.remove( 'is-open' );
			}
		} );
	} );

	/* Shadow on the header once the page scrolls. */
	var header = document.querySelector( '.site-header' );
	if ( header ) {
		var ticking = false;

		window.addEventListener(
			'scroll',
			function () {
				if ( ticking ) {
					return;
				}
				ticking = true;

				window.requestAnimationFrame( function () {
					header.classList.toggle( 'is-stuck', window.scrollY > 12 );
					ticking = false;
				} );
			},
			{ passive: true }
		);
	}
})();
