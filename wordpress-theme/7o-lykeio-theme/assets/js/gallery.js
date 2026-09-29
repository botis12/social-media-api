/**
 * Accessible lightbox.
 *
 * role="dialog" + aria-modal, focus trap, arrow keys, Escape, and the focus
 * returned to the thumbnail that opened it.
 */
(function () {
	'use strict';

	var i18n = window.lyk7Gallery || {};
	var groups = document.querySelectorAll( '[data-gallery]' );

	if ( ! groups.length ) {
		return;
	}

	var dialog = null;
	var imgEl = null;
	var capEl = null;
	var countEl = null;
	var items = [];
	var index = 0;
	var opener = null;

	function build() {
		dialog = document.createElement( 'div' );
		dialog.className = 'lightbox';
		dialog.setAttribute( 'role', 'dialog' );
		dialog.setAttribute( 'aria-modal', 'true' );
		dialog.setAttribute( 'aria-label', i18n.close || 'Gallery' );
		dialog.hidden = true;

		dialog.innerHTML =
			'<div class="lightbox__backdrop" data-close></div>' +
			'<div class="lightbox__frame">' +
			'<figure class="lightbox__figure">' +
			'<img class="lightbox__img" alt="">' +
			'<figcaption class="lightbox__caption"></figcaption>' +
			'</figure>' +
			'<p class="lightbox__count" aria-live="polite"></p>' +
			'<button type="button" class="lightbox__btn lightbox__btn--prev" data-prev>' +
			'<span class="screen-reader-text">' + ( i18n.prev || 'Previous' ) + '</span>' +
			'<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m14 6-6 6 6 6"/></svg>' +
			'</button>' +
			'<button type="button" class="lightbox__btn lightbox__btn--next" data-next>' +
			'<span class="screen-reader-text">' + ( i18n.next || 'Next' ) + '</span>' +
			'<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m10 6 6 6-6 6"/></svg>' +
			'</button>' +
			'<button type="button" class="lightbox__btn lightbox__btn--close" data-close>' +
			'<span class="screen-reader-text">' + ( i18n.close || 'Close' ) + '</span>' +
			'<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M6 6 18 18M18 6 6 18"/></svg>' +
			'</button>' +
			'</div>';

		document.body.appendChild( dialog );

		imgEl = dialog.querySelector( '.lightbox__img' );
		capEl = dialog.querySelector( '.lightbox__caption' );
		countEl = dialog.querySelector( '.lightbox__count' );

		dialog.addEventListener( 'click', function ( e ) {
			if ( e.target.closest( '[data-close]' ) ) {
				close();
			} else if ( e.target.closest( '[data-prev]' ) ) {
				show( index - 1 );
			} else if ( e.target.closest( '[data-next]' ) ) {
				show( index + 1 );
			}
		} );
	}

	function show( next ) {
		if ( ! items.length ) {
			return;
		}

		index = ( next + items.length ) % items.length;

		var link = items[ index ];
		var thumb = link.querySelector( 'img' );

		imgEl.src = link.getAttribute( 'href' );
		imgEl.alt = thumb ? thumb.getAttribute( 'alt' ) || '' : '';

		var caption = link.getAttribute( 'data-caption' ) || '';
		capEl.textContent = caption;
		capEl.hidden = ! caption;

		countEl.textContent = ( index + 1 ) + ' ' + ( i18n.of || '/' ) + ' ' + items.length;

		var single = items.length < 2;
		dialog.querySelector( '[data-prev]' ).hidden = single;
		dialog.querySelector( '[data-next]' ).hidden = single;
	}

	function open( group, link ) {
		if ( ! dialog ) {
			build();
		}

		items = Array.prototype.slice.call( group.querySelectorAll( '.mosaic__link' ) );
		opener = link;

		show( items.indexOf( link ) );

		dialog.hidden = false;
		document.body.classList.add( 'lightbox-open' );

		dialog.querySelector( '.lightbox__btn--close' ).focus();
	}

	function close() {
		if ( ! dialog ) {
			return;
		}

		dialog.hidden = true;
		document.body.classList.remove( 'lightbox-open' );
		imgEl.src = '';

		if ( opener ) {
			opener.focus();
			opener = null;
		}
	}

	Array.prototype.forEach.call( groups, function ( group ) {
		group.addEventListener( 'click', function ( e ) {
			var link = e.target.closest( '.mosaic__link' );
			if ( ! link || ! group.contains( link ) ) {
				return;
			}

			e.preventDefault();
			open( group, link );
		} );
	} );

	document.addEventListener( 'keydown', function ( e ) {
		if ( ! dialog || dialog.hidden ) {
			return;
		}

		if ( e.key === 'Escape' ) {
			close();
		} else if ( e.key === 'ArrowLeft' ) {
			show( index - 1 );
		} else if ( e.key === 'ArrowRight' ) {
			show( index + 1 );
		} else if ( e.key === 'Tab' ) {
			// Keep focus inside the dialog.
			var focusable = Array.prototype.filter.call(
				dialog.querySelectorAll( 'button:not([hidden])' ),
				function ( el ) {
					return el.offsetParent !== null;
				}
			);

			if ( ! focusable.length ) {
				return;
			}

			var first = focusable[ 0 ];
			var last = focusable[ focusable.length - 1 ];

			if ( e.shiftKey && document.activeElement === first ) {
				e.preventDefault();
				last.focus();
			} else if ( ! e.shiftKey && document.activeElement === last ) {
				e.preventDefault();
				first.focus();
			}
		}
	} );
})();
