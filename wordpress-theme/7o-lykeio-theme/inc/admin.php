<?php
/**
 * Εμφάνιση → Εγκατάσταση θέματος: re-run setup, see what exists.
 *
 * @package lyk7
 */

defined( 'ABSPATH' ) || exit;

/**
 * Register the screen.
 */
function lyk7_admin_menu() {
	add_theme_page( 'Εγκατάσταση θέματος', 'Εγκατάσταση θέματος', 'manage_options', 'lyk7-setup', 'lyk7_admin_page' );
}
add_action( 'admin_menu', 'lyk7_admin_menu' );

/**
 * Render the screen and handle the button.
 */
function lyk7_admin_page() {
	$log = array();

	if ( isset( $_POST['lyk7_run'] ) && check_admin_referer( 'lyk7_setup' ) ) {
		$log = lyk7_install( ! empty( $_POST['lyk7_content'] ) );
	}

	$counts = array(
		'Ανακοινώσεις'   => wp_count_posts( 'anakoinosi' )->publish,
		'Δραστηριότητες' => wp_count_posts( 'drastiriotita' )->publish,
		'Έγγραφα'        => wp_count_posts( 'eggrafo' )->publish,
		'Φωτογραφίες'    => wp_count_posts( 'gallery_item' )->publish,
		'Σελίδες'        => wp_count_posts( 'page' )->publish,
	);
	?>
	<div class="wrap">
		<h1>Εγκατάσταση θέματος 7ο ΓΕΛ Ιλίου</h1>

		<?php if ( $log ) : ?>
			<div class="notice notice-success"><p><strong>Ολοκληρώθηκε.</strong></p><ul style="list-style:disc;padding-left:20px">
				<?php foreach ( $log as $line ) : ?>
					<li><?php echo esc_html( $line ); ?></li>
				<?php endforeach; ?>
			</ul></div>
		<?php endif; ?>

		<p>Το θέμα δημιουργεί αυτόματα τις σελίδες, τις κατηγορίες και τα μενού κατά την ενεργοποίηση. Αν κάτι λείπει, πατήστε ξανά το κουμπί — τίποτα δεν δημιουργείται διπλό.</p>

		<table class="widefat striped" style="max-width:480px">
			<tbody>
			<?php foreach ( $counts as $label => $count ) : ?>
				<tr><td><?php echo esc_html( $label ); ?></td><td><strong><?php echo (int) $count; ?></strong></td></tr>
			<?php endforeach; ?>
				<tr><td>Μόνιμοι σύνδεσμοι</td><td><strong><?php echo esc_html( get_option( 'permalink_structure' ) ? get_option( 'permalink_structure' ) : 'Απλοί (?p=) — πρέπει να αλλάξουν' ); ?></strong></td></tr>
			</tbody>
		</table>

		<form method="post" style="margin-top:20px">
			<?php wp_nonce_field( 'lyk7_setup' ); ?>
			<p><label><input type="checkbox" name="lyk7_content" value="1" <?php checked( ! $counts['Ανακοινώσεις'] ); ?>> Εισαγωγή και του περιεχομένου (ανακοινώσεις, δράσεις, έγγραφα, φωτογραφίες)</label></p>
			<p><button type="submit" name="lyk7_run" value="1" class="button button-primary button-hero">Εκτέλεση εγκατάστασης</button></p>
		</form>

		<h2>Πού αλλάζει τι</h2>
		<ul style="list-style:disc;padding-left:20px">
			<li><strong>Τηλέφωνα, email, ωράριο, κείμενα αρχικής:</strong> Εμφάνιση → Προσαρμογή → 7ο ΓΕΛ Ιλίου</li>
			<li><strong>Λογότυπο:</strong> Εμφάνιση → Προσαρμογή → Ταυτότητα ιστότοπου</li>
			<li><strong>Μενού:</strong> Εμφάνιση → Μενού</li>
			<li><strong>Ανακοινώσεις / Δραστηριότητες / Έγγραφα / Φωτογραφίες:</strong> από τα αντίστοιχα μενού αριστερά</li>
		</ul>
	</div>
	<?php
}

/**
 * Notice after activation, pointing to the setup screen.
 */
function lyk7_admin_notice() {
	if ( ! current_user_can( 'manage_options' ) ) {
		return;
	}
	$screen = get_current_screen();
	if ( $screen && 'themes' === $screen->id ) {
		printf(
			'<div class="notice notice-success is-dismissible"><p><strong>7ο ΓΕΛ Ιλίου:</strong> οι σελίδες, τα μενού και το περιεχόμενο δημιουργήθηκαν. <a href="%s">Έλεγχος εγκατάστασης</a> · <a href="%s">Προβολή ιστότοπου</a></p></div>',
			esc_url( admin_url( 'themes.php?page=lyk7-setup' ) ),
			esc_url( home_url( '/' ) )
		);
	}
}
add_action( 'admin_notices', 'lyk7_admin_notice' );

/**
 * Pages get an excerpt box (used as the intro line under the title).
 */
function lyk7_page_excerpts() {
	add_post_type_support( 'page', 'excerpt' );
}
add_action( 'init', 'lyk7_page_excerpts' );
