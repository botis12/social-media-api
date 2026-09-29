<?php
/**
 * Not found.
 *
 * @package lyk7
 */

get_header();
?>
<div class="wrap section error-404">
	<p class="eyebrow">Σφάλμα 404</p>
	<h1 class="error-404__title">Η σελίδα δεν βρέθηκε</h1>
	<p class="error-404__text">Ο σύνδεσμος μπορεί να έχει αλλάξει ή η σελίδα να έχει μεταφερθεί. Δοκιμάστε την αναζήτηση ή μία από τις συντομεύσεις.</p>
	<div class="error-404__search"><?php get_search_form(); ?></div>

	<ul class="quick-grid quick-grid--compact">
		<?php foreach ( array_slice( lyk7_parse_lines( lyk7_opt( 'quick' ), 4 ), 0, 4 ) as $lyk7_tile ) : ?>
			<li class="quick-tile">
				<a href="<?php echo esc_url( lyk7_resolve_url( $lyk7_tile[2] ) ); ?>">
					<span class="quick-tile__icon"><?php lyk7_icon( $lyk7_tile[3] ? $lyk7_tile[3] : 'arrow', 26 ); ?></span>
					<span class="quick-tile__label"><?php echo esc_html( $lyk7_tile[0] ); ?></span>
				</a>
			</li>
		<?php endforeach; ?>
	</ul>
</div>
<?php
get_footer();
