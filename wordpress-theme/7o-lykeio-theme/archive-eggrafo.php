<?php
/**
 * Documents: searchable, filterable list.
 *
 * @package lyk7
 */

get_header();
lyk7_breadcrumbs();
lyk7_page_head( 'Έγγραφα και αρχεία', 'Αρχείο', 'Κανονισμοί, εκθέσεις αξιολόγησης, προγράμματα εξετάσεων, εγκύκλιοι και έντυπα. Φιλτράρετε ανά κατηγορία ή σχολικό έτος, ή αναζητήστε με τον τίτλο.' );

// phpcs:disable WordPress.Security.NonceVerification.Recommended
$lyk7_kind = isset( $_GET['eidos'] ) ? sanitize_title( wp_unslash( $_GET['eidos'] ) ) : '';
$lyk7_year = isset( $_GET['etos'] ) ? sanitize_title( wp_unslash( $_GET['etos'] ) ) : '';
// phpcs:enable
$lyk7_kinds = get_terms( array( 'taxonomy' => 'eidos_eggrafou', 'hide_empty' => true ) );
$lyk7_years = get_terms( array( 'taxonomy' => 'sxoliko_etos', 'hide_empty' => true, 'orderby' => 'name', 'order' => 'DESC' ) );
?>
<div class="wrap section">
	<form class="doc-filters" method="get" action="<?php echo esc_url( get_post_type_archive_link( 'eggrafo' ) ); ?>" data-doc-filters>
		<?php if ( ! get_option( 'permalink_structure' ) ) : ?>
			<input type="hidden" name="post_type" value="eggrafo">
		<?php endif; ?>
		<div class="doc-filters__field">
			<label for="doc-search">Αναζήτηση στον τίτλο</label>
			<input type="search" id="doc-search" data-doc-search placeholder="π.χ. κανονισμός, πανελλαδικές…" autocomplete="off">
		</div>
		<div class="doc-filters__field">
			<label for="doc-kind">Κατηγορία</label>
			<select id="doc-kind" name="eidos" data-doc-kind>
				<option value="">Όλες οι κατηγορίες</option>
				<?php foreach ( (array) $lyk7_kinds as $lyk7_t ) : ?>
					<option value="<?php echo esc_attr( $lyk7_t->slug ); ?>" <?php selected( $lyk7_kind, $lyk7_t->slug ); ?>><?php echo esc_html( $lyk7_t->name ); ?></option>
				<?php endforeach; ?>
			</select>
		</div>
		<div class="doc-filters__field">
			<label for="doc-year">Σχολικό έτος</label>
			<select id="doc-year" name="etos" data-doc-year>
				<option value="">Όλα τα έτη</option>
				<?php foreach ( (array) $lyk7_years as $lyk7_t ) : ?>
					<option value="<?php echo esc_attr( $lyk7_t->slug ); ?>" <?php selected( $lyk7_year, $lyk7_t->slug ); ?>><?php echo esc_html( $lyk7_t->name ); ?></option>
				<?php endforeach; ?>
			</select>
		</div>
		<div class="doc-filters__actions">
			<button type="submit" class="btn btn--primary">Εφαρμογή</button>
		</div>
		<p class="doc-filters__status" role="status" aria-live="polite" data-doc-status></p>
	</form>

	<?php if ( have_posts() ) : ?>
		<ul class="doc-list doc-list--full" data-doc-list>
			<?php
			while ( have_posts() ) :
				the_post();
				get_template_part( 'template-parts/doc-row' );
			endwhile;
			?>
		</ul>
	<?php endif; ?>
	<p class="doc-empty" data-doc-empty <?php echo have_posts() ? 'hidden' : ''; ?>>Δεν βρέθηκαν έγγραφα με αυτά τα κριτήρια.</p>
</div>
<?php
get_footer();
