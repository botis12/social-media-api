<?php
/**
 * Editor fields: urgency, deadline, attachments, event date, place, file.
 *
 * Classic meta boxes work in both the block editor and the classic editor,
 * with no plugin required.
 *
 * @package lyk7
 */

defined( 'ABSPATH' ) || exit;

/**
 * Register the boxes.
 */
function lyk7_add_meta_boxes() {
	add_meta_box( 'lyk7-announcement', 'Στοιχεία ανακοίνωσης', 'lyk7_box_announcement', 'anakoinosi', 'side', 'high' );
	add_meta_box( 'lyk7-attachments', 'Συνημμένα αρχεία', 'lyk7_box_attachments', 'anakoinosi', 'normal', 'default' );
	add_meta_box( 'lyk7-activity', 'Στοιχεία δραστηριότητας', 'lyk7_box_activity', 'drastiriotita', 'side', 'high' );
	add_meta_box( 'lyk7-document', 'Αρχείο εγγράφου', 'lyk7_box_document', 'eggrafo', 'normal', 'high' );
}
add_action( 'add_meta_boxes', 'lyk7_add_meta_boxes' );

/**
 * Admin script for the media pickers.
 *
 * @param string $hook Screen hook.
 */
function lyk7_admin_assets( $hook ) {
	if ( ! in_array( $hook, array( 'post.php', 'post-new.php' ), true ) ) {
		return;
	}

	$screen = get_current_screen();
	if ( ! $screen || ! in_array( $screen->post_type, array( 'anakoinosi', 'eggrafo' ), true ) ) {
		return;
	}

	wp_enqueue_media();
	wp_enqueue_script( 'lyk7-admin', LYK7_URI . '/assets/js/admin.js', array( 'jquery' ), LYK7_VERSION, true );
	wp_localize_script(
		'lyk7-admin',
		'lyk7Admin',
		array(
			'pickFile'  => 'Επιλογή αρχείου',
			'pickFiles' => 'Επιλογή συνημμένων',
			'use'       => 'Χρήση',
			'remove'    => 'Αφαίρεση',
		)
	);
}
add_action( 'admin_enqueue_scripts', 'lyk7_admin_assets' );

/**
 * Announcement: urgent flag and deadline.
 *
 * @param WP_Post $post Post.
 */
function lyk7_box_announcement( $post ) {
	wp_nonce_field( 'lyk7_meta', 'lyk7_meta_nonce' );
	$urgent   = (bool) get_post_meta( $post->ID, '_lyk7_urgent', true );
	$deadline = get_post_meta( $post->ID, '_lyk7_deadline', true );
	?>
	<p>
		<label>
			<input type="checkbox" name="lyk7_urgent" value="1" <?php checked( $urgent ); ?>>
			<strong>Επείγον</strong> — καρφιτσώνεται πρώτη στην αρχική
		</label>
	</p>
	<p>
		<label for="lyk7_deadline"><strong>Προθεσμία</strong> (προαιρετικά)</label><br>
		<input type="date" id="lyk7_deadline" name="lyk7_deadline" value="<?php echo esc_attr( $deadline ); ?>" style="width:100%">
		<span class="description">Η πλησιέστερη προθεσμία εμφανίζεται στη λωρίδα «Σήμερα στο σχολείο».</span>
	</p>
	<?php
}

/**
 * Announcement: attached files.
 *
 * @param WP_Post $post Post.
 */
function lyk7_box_attachments( $post ) {
	$ids = lyk7_attachment_ids( $post->ID );
	?>
	<div class="lyk7-files" data-lyk7-files>
		<input type="hidden" name="lyk7_attachments" value="<?php echo esc_attr( implode( ',', $ids ) ); ?>" data-lyk7-files-input>
		<ul data-lyk7-files-list style="margin:0 0 10px">
			<?php foreach ( $ids as $id ) : ?>
				<li data-id="<?php echo (int) $id; ?>">
					<span class="dashicons dashicons-media-default"></span>
					<?php echo esc_html( get_the_title( $id ) ); ?>
					<button type="button" class="button-link" data-lyk7-files-remove>Αφαίρεση</button>
				</li>
			<?php endforeach; ?>
		</ul>
		<button type="button" class="button" data-lyk7-files-add>Προσθήκη αρχείων</button>
		<p class="description">PDF, Word, Excel κ.λπ. Εμφανίζονται κάτω από το κείμενο της ανακοίνωσης με το μέγεθός τους.</p>
	</div>
	<?php
}

/**
 * Activity: event date and place.
 *
 * @param WP_Post $post Post.
 */
function lyk7_box_activity( $post ) {
	wp_nonce_field( 'lyk7_meta', 'lyk7_meta_nonce' );
	$date  = get_post_meta( $post->ID, '_lyk7_event_date', true );
	$place = get_post_meta( $post->ID, '_lyk7_place', true );
	?>
	<p>
		<label for="lyk7_event_date"><strong>Ημερομηνία δράσης</strong></label><br>
		<input type="date" id="lyk7_event_date" name="lyk7_event_date" value="<?php echo esc_attr( $date ); ?>" style="width:100%">
		<span class="description">Αν μείνει κενή, χρησιμοποιείται η ημερομηνία δημοσίευσης.</span>
	</p>
	<p>
		<label for="lyk7_place"><strong>Τόπος</strong></label><br>
		<input type="text" id="lyk7_place" name="lyk7_place" value="<?php echo esc_attr( $place ); ?>" style="width:100%" placeholder="π.χ. 7ο ΓΕΛ Ιλίου">
	</p>
	<?php
}

/**
 * Document: uploaded file or external link.
 *
 * @param WP_Post $post Post.
 */
function lyk7_box_document( $post ) {
	wp_nonce_field( 'lyk7_meta', 'lyk7_meta_nonce' );
	$file_id  = (int) get_post_meta( $post->ID, '_lyk7_file_id', true );
	$file_url = get_post_meta( $post->ID, '_lyk7_file_url', true );
	?>
	<div data-lyk7-file>
		<input type="hidden" name="lyk7_file_id" value="<?php echo $file_id ? (int) $file_id : ''; ?>" data-lyk7-file-input>
		<p data-lyk7-file-name>
			<?php
			if ( $file_id ) {
				echo '<strong>' . esc_html( get_the_title( $file_id ) ) . '</strong> — ' . esc_html( basename( (string) get_attached_file( $file_id ) ) );
			} else {
				echo '<em>Δεν έχει επιλεγεί αρχείο.</em>';
			}
			?>
		</p>
		<p>
			<button type="button" class="button button-primary" data-lyk7-file-pick>Επιλογή / μεταφόρτωση αρχείου</button>
			<button type="button" class="button" data-lyk7-file-clear <?php echo $file_id ? '' : 'hidden'; ?>>Αφαίρεση</button>
		</p>
	</div>
	<hr>
	<p>
		<label for="lyk7_file_url"><strong>Ή εξωτερικός σύνδεσμος</strong></label><br>
		<input type="url" id="lyk7_file_url" name="lyk7_file_url" value="<?php echo esc_attr( $file_url ); ?>" style="width:100%" placeholder="https://…">
		<span class="description">Χρησιμοποιείται μόνο αν δεν έχει επιλεγεί αρχείο.</span>
	</p>
	<p class="description">Ορίστε δεξιά την <strong>Κατηγορία εγγράφου</strong> και το <strong>Σχολικό έτος</strong> για τα φίλτρα της σελίδας «Έγγραφα».</p>
	<?php
}

/**
 * Save all fields.
 *
 * @param int     $post_id Post ID.
 * @param WP_Post $post    Post.
 */
function lyk7_save_meta( $post_id, $post ) {
	if ( defined( 'DOING_AUTOSAVE' ) && DOING_AUTOSAVE ) {
		return;
	}
	if ( ! isset( $_POST['lyk7_meta_nonce'] ) || ! wp_verify_nonce( sanitize_key( $_POST['lyk7_meta_nonce'] ), 'lyk7_meta' ) ) {
		return;
	}
	if ( ! current_user_can( 'edit_post', $post_id ) ) {
		return;
	}

	switch ( $post->post_type ) {
		case 'anakoinosi':
			update_post_meta( $post_id, '_lyk7_urgent', empty( $_POST['lyk7_urgent'] ) ? 0 : 1 );
			update_post_meta( $post_id, '_lyk7_deadline', lyk7_clean_date( wp_unslash( $_POST['lyk7_deadline'] ?? '' ) ) );
			$ids = array_filter( array_map( 'absint', explode( ',', sanitize_text_field( wp_unslash( $_POST['lyk7_attachments'] ?? '' ) ) ) ) );
			update_post_meta( $post_id, '_lyk7_attachments', implode( ',', $ids ) );
			break;

		case 'drastiriotita':
			update_post_meta( $post_id, '_lyk7_event_date', lyk7_clean_date( wp_unslash( $_POST['lyk7_event_date'] ?? '' ) ) );
			update_post_meta( $post_id, '_lyk7_place', sanitize_text_field( wp_unslash( $_POST['lyk7_place'] ?? '' ) ) );
			break;

		case 'eggrafo':
			update_post_meta( $post_id, '_lyk7_file_id', absint( $_POST['lyk7_file_id'] ?? 0 ) );
			update_post_meta( $post_id, '_lyk7_file_url', esc_url_raw( wp_unslash( $_POST['lyk7_file_url'] ?? '' ) ) );
			break;
	}
}
add_action( 'save_post', 'lyk7_save_meta', 10, 2 );

/**
 * Accept only Y-m-d.
 *
 * @param string $value Raw value.
 * @return string
 */
function lyk7_clean_date( $value ) {
	$value = sanitize_text_field( (string) $value );
	return preg_match( '/^\d{4}-\d{2}-\d{2}$/', $value ) ? $value : '';
}

/**
 * Attachment IDs stored on an announcement.
 *
 * @param int $post_id Post ID.
 * @return int[]
 */
function lyk7_attachment_ids( $post_id ) {
	$raw = (string) get_post_meta( $post_id, '_lyk7_attachments', true );
	return array_values( array_filter( array_map( 'absint', explode( ',', $raw ) ) ) );
}
