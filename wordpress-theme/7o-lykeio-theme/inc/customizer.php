<?php
/**
 * Customizer: school details, homepage texts, timetable, quick links.
 * Εμφάνιση → Προσαρμογή → «Στοιχεία σχολείου» / «Αρχική σελίδα».
 *
 * @package lyk7
 */

defined( 'ABSPATH' ) || exit;

/**
 * Defaults — the content of the current site.
 *
 * @return array
 */
function lyk7_defaults() {
	return array(
		'address'       => 'Βυτιβίλια 50-52, 131 22 Ίλιον',
		'phones'        => "Διεύθυνση σχολείου | 210 2690888, 212 8098053\nΓραφείο Καθηγητών | 210 2692380",
		'email'         => 'mail@7lyk-iliou.att.sch.gr',
		'summer_note'   => 'Ιούλιο και Αύγουστο το σχολείο είναι ανοιχτό κάθε Πέμπτη 08:00-14:00.',
		'map_url'       => 'https://www.openstreetmap.org/?mlat=38.0293904&mlon=23.7126109#map=17/38.0293904/23.7126109',
		'timetable'     => "1η ώρα | 08:15 | 09:00\n2η ώρα | 09:05 | 09:50\n3η ώρα | 10:00 | 10:45\n4η ώρα | 10:55 | 11:40\n5η ώρα | 11:50 | 12:35\n6η ώρα | 12:45 | 13:25\n7η ώρα | 13:30 | 14:10",
		'hero_eyebrow'  => 'Δημόσιο Γενικό Λύκειο · Ίλιον',
		'hero_top'      => '7ο Γενικό Λύκειο',
		'hero_main'     => 'Ιλίου',
		'hero_text'     => 'Ένα σχολείο που φροντίζει τους χώρους του και τους ανθρώπους του. Ανακοινώσεις, έγγραφα και η καθημερινή ζωή του Λυκείου, σε ένα σημείο.',
		'hero_alt'      => 'Η πρόσοψη του 7ου ΓΕΛ Ιλίου με τις πικροδάφνες στην είσοδο',
		'about_lead'    => 'Το νεότερο Λύκειο του Ιλίου, με ευήλιες αίθουσες, εργαστήρια, δανειστική βιβλιοθήκη και αμφιθέατρο — και κοινόχρηστους χώρους που το ξεχωρίζουν.',
		'timeline'      => "1995 | Ανεγείρεται το κτίριο στην οδό Βυτιβίλια 50-52.\n1998 | Ιδρύεται ως 8ο Ενιαίο Λύκειο, με μετεξέλιξη του 2ου ΤΕΛ Ιλίου.\n1999 | Συγχωνεύεται και παραμένει ως 7ο Ενιαίο Λύκειο Ιλίου.\n2006 | Στο κτίριο στεγάζεται και η Γ΄ ΕΛΜΕ Αθήνας.",
		'quick'         => "Ωράριο | Οι 7 διδακτικές ώρες | /mathites-goneis/#orario | clock\nΕξετάσεις | Προγράμματα και ύλη | /eggrafa/?eidos=exetaseis | pen\nΈγγραφα | Όλο το αρχείο | /eggrafa/ | file\nΕγγραφές | e-εγγραφές και έντυπα | /eggrafa/?eidos=eggrafes | users\nΚανονισμός | Σχολικός κανονισμός | /eggrafa/?eidos=kanonistika | book\nΓονείς | Ώρες επικοινωνίας | /eggrafa/?eidos=goneis | mail\nΨηφιακή τάξη | Webex, e-me, sch.gr | /eggrafa/?eidos=psifiaka-ergaleia | flask\nΕπικοινωνία | Τηλέφωνα και χάρτης | /epikoinonia/ | phone",
		'docs_lede'     => 'Κανονισμοί, προγράμματα εξετάσεων, εγκύκλιοι και έντυπα — με αναζήτηση και φίλτρα ανά κατηγορία και σχολικό έτος.',
		'show_preview'  => '',
	);
}

/**
 * Register panels, sections and controls.
 *
 * @param WP_Customize_Manager $wp_customize Manager.
 */
function lyk7_customize_register( $wp_customize ) {
	$wp_customize->add_panel( 'lyk7', array( 'title' => '7ο ΓΕΛ Ιλίου', 'priority' => 30 ) );

	$sections = array(
		'lyk7_school' => array(
			'title'  => 'Στοιχεία σχολείου',
			'fields' => array(
				'address'     => array( 'Διεύθυνση', 'text' ),
				'phones'      => array( 'Τηλέφωνα — μία γραμμή ανά τηλέφωνο: Ετικέτα | αριθμός, αριθμός', 'textarea' ),
				'email'       => array( 'Email', 'email' ),
				'summer_note' => array( 'Σημείωση καλοκαιρινού ωραρίου', 'text' ),
				'map_url'     => array( 'Σύνδεσμος χάρτη', 'url' ),
				'timetable'   => array( 'Ωράριο — μία γραμμή ανά ώρα: Ώρα | Έναρξη | Λήξη', 'textarea' ),
			),
		),
		'lyk7_home'   => array(
			'title'  => 'Αρχική σελίδα',
			'fields' => array(
				'hero_eyebrow' => array( 'Κεντρική εικόνα — μικρός τίτλος', 'text' ),
				'hero_top'     => array( 'Τίτλος — πρώτη γραμμή', 'text' ),
				'hero_main'    => array( 'Τίτλος — μεγάλη γραμμή', 'text' ),
				'hero_text'    => array( 'Κείμενο', 'textarea' ),
				'hero_alt'     => array( 'Περιγραφή εικόνας (alt)', 'text' ),
				'quick'        => array( 'Γρήγορη πρόσβαση — Τίτλος | Περιγραφή | Σύνδεσμος | εικονίδιο (' . implode( ', ', lyk7_icon_names() ) . ')', 'textarea' ),
				'about_lead'   => array( 'Ενότητα «Το σχολείο μας» — κείμενο', 'textarea' ),
				'timeline'     => array( 'Χρονολόγιο — Έτος | Κείμενο', 'textarea' ),
				'docs_lede'    => array( 'Ενότητα «Έγγραφα» — κείμενο', 'textarea' ),
			),
		),
	);

	$defaults = lyk7_defaults();

	foreach ( $sections as $section_id => $section ) {
		$wp_customize->add_section( $section_id, array( 'title' => $section['title'], 'panel' => 'lyk7' ) );

		foreach ( $section['fields'] as $key => $field ) {
			$wp_customize->add_setting(
				'lyk7_' . $key,
				array(
					'default'           => $defaults[ $key ],
					'sanitize_callback' => 'textarea' === $field[1] ? 'sanitize_textarea_field' : ( 'url' === $field[1] ? 'esc_url_raw' : 'sanitize_text_field' ),
				)
			);
			$wp_customize->add_control(
				'lyk7_' . $key,
				array(
					'label'   => $field[0],
					'section' => $section_id,
					'type'    => $field[1],
				)
			);
		}
	}

	$wp_customize->add_setting( 'lyk7_use_wp_menus', array( 'default' => false, 'sanitize_callback' => 'wp_validate_boolean' ) );
	$wp_customize->add_control(
		'lyk7_use_wp_menus',
		array(
			'label'       => 'Χρήση των μενού του WordPress',
			'description' => 'Αφήστε το ατσέκαρτο: το θέμα δείχνει μόνο του όλες τις σελίδες. Τσεκάρετε μόνο αν θέλετε να φτιάχνετε το μενού χειροκίνητα από Εμφάνιση → Μενού.',
			'section'     => 'lyk7_school',
			'type'        => 'checkbox',
		)
	);

	$images = array(
		'hero_image'   => 'Κεντρική εικόνα αρχικής',
		'about_image'  => '«Το σχολείο μας» — μεγάλη εικόνα',
		'about_image2' => '«Το σχολείο μας» — μικρή εικόνα',
	);
	foreach ( $images as $key => $label ) {
		$wp_customize->add_setting( 'lyk7_' . $key, array( 'sanitize_callback' => 'absint' ) );
		$wp_customize->add_control(
			new WP_Customize_Media_Control(
				$wp_customize,
				'lyk7_' . $key,
				array(
					'label'     => $label,
					'section'   => 'lyk7_home',
					'mime_type' => 'image',
				)
			)
		);
	}
}
add_action( 'customize_register', 'lyk7_customize_register' );
