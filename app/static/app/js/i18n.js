/* ASRAMAku language switch: English (default) or Bahasa Melayu.
 *
 * The pages are written in English. When Malay is picked, this script swaps the
 * text it knows (the lists below) for Malay, and swaps it back when English is picked.
 * Names, IDs, dates and anything else not in the lists stay as they are.
 * The choice is remembered on this device (localStorage).
 *
 * To translate a new piece of text, add it to WORDS (exact text) or PATTERNS
 * (text with a name, date or number inside it). Nothing else needs to change.
 */
(function () {
    'use strict';

    var STORAGE_KEY = 'asramakuLang';

    // Exact text, English -> Malay
    var WORDS = {
        // Top bar, menus, footer
        'Pending outing requests': 'Permohonan outing belum diproses',
        'No pending requests': 'Tiada permohonan belum diproses',
        'View all requests': 'Lihat semua permohonan',
        'Account menu': 'Menu akaun',
        'ASRAMAku home': 'Laman utama ASRAMAku',
        'Administrator': 'Pentadbir',
        'Guard': 'Pengawal',
        'Warden': 'Warden',
        'Student': 'Pelajar',
        'Profile': 'Profil',
        'Outing Time Settings': 'Tetapan Masa Outing',
        'Test Form': 'Borang Ujian',
        'Logout': 'Log Keluar',
        'Toggle navigation': 'Buka atau tutup menu',
        'Dashboard': 'Papan Pemuka',
        'Students': 'Pelajar',
        'Requests': 'Permohonan',
        'Outing Request': 'Permohonan Outing',
        'Home Leave': 'Cuti Pulang',
        'Outing': 'Outing',
        'Staff Login': 'Log Masuk Staf',
        'Log out of ASRAMAku?': 'Log keluar daripada ASRAMAku?',
        "You'll need your username and password to sign back in.": 'Anda perlukan nama pengguna dan kata laluan untuk log masuk semula.',
        'Cancel': 'Batal',
        'Yes, Logout': 'Ya, Log Keluar',
        'Close': 'Tutup',
        'OK': 'OK',
        '© 2026 ASRAMAku. Built for smoother student monitoring.': '© 2026 ASRAMAku. Dibina untuk pemantauan pelajar yang lebih lancar.',
        '© 2026 ASRAMAku. Built for smoother student monitoring. All rights reserved': '© 2026 ASRAMAku. Dibina untuk pemantauan pelajar yang lebih lancar. Hak cipta terpelihara.',

        // Outing time settings
        'Outing Return Time': 'Masa Kembali Outing',
        'Outing Return Time help: The latest time all students must be checked back in for the day (e.g., 22:00).': 'Bantuan Masa Kembali Outing: Masa paling lewat semua pelajar mesti daftar masuk semula pada hari itu (cth. 22:00).',
        'The latest time all students must be checked back in for the day (e.g., 22:00).': 'Masa paling lewat semua pelajar mesti daftar masuk semula pada hari itu (cth. 22:00).',
        'Thu - Sat': 'Kha - Sab',
        'Sun - Wed': 'Ahd - Rab',
        'These are the defaults when no return time is saved.': 'Ini masa asal jika tiada masa kembali disimpan.',
        'Save Settings': 'Simpan Tetapan',
        'Please enter a valid return time in HH:MM format.': 'Sila masukkan masa kembali yang sah dalam format HH:MM.',
        'Outing settings saved.': 'Tetapan outing disimpan.',
        'Outing time settings saved.': 'Tetapan masa outing disimpan.',
        'Outing time settings saved successfully.': 'Tetapan masa outing berjaya disimpan.',
        'Unable to save settings.': 'Tidak dapat menyimpan tetapan.',
        'Something went wrong while saving settings.': 'Ralat berlaku semasa menyimpan tetapan.',
        'Please enter valid values for the outing settings.': 'Sila masukkan nilai yang sah untuk tetapan outing.',
        'Return time is required.': 'Masa kembali diperlukan.',

        // Login
        'Every outing, every return, in one place.': 'Setiap keluar, setiap kembali, di satu tempat.',
        'The hostel outing system for TVETMARA Sungai Petani. Scan cards at the entrance, approve home leave, and catch late returns as they happen.': 'Sistem outing asrama untuk TVETMARA Sungai Petani. Imbas kad di pintu masuk, luluskan cuti pulang, dan kesan pelajar lewat kembali serta-merta.',
        'RFID check in and check out at the guard post': 'Daftar masuk dan keluar RFID di pondok pengawal',
        'Home leave requests approved in one click': 'Permohonan cuti pulang diluluskan dengan satu klik',
        'Late returns flagged against the outing return time': 'Kelewatan kembali ditanda mengikut masa kembali outing',
        'Welcome back': 'Selamat kembali',
        'Sign in with your warden or guard account.': 'Log masuk dengan akaun warden atau pengawal anda.',
        'Username': 'Nama pengguna',
        'Password': 'Kata laluan',
        'Enter your username': 'Masukkan nama pengguna anda',
        'Enter your password': 'Masukkan kata laluan anda',
        'Show password': 'Tunjuk kata laluan',
        'Hide password': 'Sembunyi kata laluan',
        'Login': 'Log Masuk',
        'Student?': 'Pelajar?',
        "You don't need an account.": 'Anda tidak perlukan akaun.',
        'Apply for home leave here': 'Mohon cuti pulang di sini',
        'Invalid username or password.': 'Nama pengguna atau kata laluan tidak sah.',
        'You have been logged out successfully.': 'Anda telah berjaya log keluar.',

        // Student portal (home leave)
        'Student portal': 'Portal pelajar',
        'Home leave permit': 'Permit cuti pulang',
        "Apply here before going home. Short outings don't need a permit, just scan your card at the hostel entrance.": 'Mohon di sini sebelum pulang ke rumah. Outing biasa tidak perlukan permit, cuma imbas kad anda di pintu masuk asrama.',
        'Verify identity': 'Sahkan identiti',
        'Leave details': 'Butiran cuti',
        'Step 1: Verify your identity': 'Langkah 1: Sahkan identiti anda',
        'Step 2: Home leave details': 'Langkah 2: Butiran cuti pulang',
        'Matric ID or IC Number': 'No. Matrik atau No. Kad Pengenalan',
        'Matric ID, IC Number or RFID card': 'No. Matrik, No. Kad Pengenalan atau kad RFID',
        'No record found': 'Rekod tidak dijumpai',
        'Nothing entered': 'Tiada maklumat dimasukkan',
        'Enter your matric ID or IC number, or wave your card.': 'Masukkan no. matrik atau no. kad pengenalan anda, atau imbas kad anda.',
        'Home leave blocked': 'Cuti pulang disekat',
        'Verification failed': 'Pengesahan gagal',
        'Please try again.': 'Sila cuba lagi.',
        'Connection problem': 'Masalah sambungan',
        'Matric ID, IC number or card not found.': 'No. matrik, no. kad pengenalan atau kad tidak dijumpai.',
        'Matric ID, IC number or card not found. Please check and try again.': 'No. matrik, no. kad pengenalan atau kad tidak dijumpai. Sila semak dan cuba lagi.',
        'Matric ID, IC number or card not found in our records.': 'No. matrik, no. kad pengenalan atau kad tiada dalam rekod kami.',
        'e.g. 33342125xxxx': 'cth. 33342125xxxx',
        'Forgot your matric ID? Enter your IC number instead.': 'Lupa no. matrik? Masukkan no. kad pengenalan anda.',
        'Continue': 'Teruskan',
        'Verified': 'Disahkan',
        'Not you?': 'Bukan anda?',
        'Your recent requests': 'Permohonan terkini anda',
        'Destination': 'Destinasi',
        'Where are you going?': 'Ke mana anda pergi?',
        'Purpose': 'Tujuan',
        'Reason for your home leave': 'Sebab cuti pulang anda',
        'Leave date': 'Tarikh keluar',
        'Leave time': 'Masa keluar',
        'Return date': 'Tarikh kembali',
        'Hour': 'Jam',
        'Minute': 'Minit',
        'AM or PM': 'AM atau PM',
        'Submit request': 'Hantar permohonan',
        "You'll get an email once the warden decides.": 'Anda akan terima e-mel selepas warden membuat keputusan.',
        'Scan your card at the entrance when you leave and return.': 'Imbas kad anda di pintu masuk semasa keluar dan kembali.',
        'Hostel staff?': 'Staf asrama?',
        'Log in here': 'Log masuk di sini',
        'Submit home leave request?': 'Hantar permohonan cuti pulang?',
        'Leave:': 'Keluar:',
        'Return:': 'Kembali:',
        'Yes, submit': 'Ya, hantar',
        'Enter your matric ID or IC Number.': 'Masukkan no. matrik atau no. kad pengenalan anda.',
        'Verification failed.': 'Pengesahan gagal.',
        'Could not reach the server. Try again.': 'Tidak dapat menghubungi pelayan. Cuba lagi.',
        'Matric ID or IC number not found. Please check and try again.': 'No. matrik atau no. kad pengenalan tidak dijumpai. Sila semak dan cuba lagi.',
        'Matric ID or IC number not found in our records.': 'No. matrik atau no. kad pengenalan tiada dalam rekod kami.',
        'Please fill in every field of the home leave form.': 'Sila isi semua ruangan borang cuti pulang.',
        'Home leave needs a return date after the leave date.': 'Cuti pulang memerlukan tarikh kembali selepas tarikh keluar.',
        "Home leave request submitted. You'll get an email once the warden decides.": 'Permohonan cuti pulang telah dihantar. Anda akan terima e-mel selepas warden membuat keputusan.',

        // Request statuses
        'Pending': 'Menunggu',
        'Approved': 'Diluluskan',
        'Rejected': 'Ditolak',
        'Used': 'Digunakan',
        'None': 'Tiada',
        'approved': 'diluluskan',
        'rejected': 'ditolak',

        // Dashboard
        'Student monitoring': 'Pemantauan pelajar',
        'Operations dashboard': 'Papan pemuka operasi',
        'Track attendance, outing status, and late arrivals in one streamlined workspace designed for quick decisions.': 'Pantau kehadiran, status outing dan kelewatan dalam satu ruang kerja yang ringkas untuk keputusan pantas.',
        'Present': 'Hadir',
        'Currently out': 'Sedang keluar',
        'Late': 'Lewat',
        'Filter': 'Tapis',
        'Show only students who were late on the selected date': 'Tunjuk pelajar yang lewat pada tarikh dipilih sahaja',
        'Check in / out': 'Daftar masuk / keluar',
        'Today': 'Hari ini',
        'Enter Student ID / ID Card / RFID': 'Masukkan ID Pelajar / Kad Pengenalan / RFID',
        'Scan or type the student identifier': 'Imbas atau taip ID pelajar',
        'Submit': 'Hantar',
        'Reader ready': 'Pengimbas sedia',
        'Press Enter to submit': 'Tekan Enter untuk hantar',
        'Scanning toggles in and out': 'Imbasan menukar masuk dan keluar',
        'Status guide': 'Panduan status',
        'In (On time)': 'Masuk (Tepat masa)',
        'In (Late)': 'Masuk (Lewat)',
        'Out (On time)': 'Keluar (Tepat masa)',
        'Out (Late)': 'Keluar (Lewat)',
        'In': 'Masuk',
        'Out': 'Keluar',
        'Back before the return time': 'Kembali sebelum masa ditetapkan',
        'Back after the return time': 'Kembali selepas masa ditetapkan',
        'Still outside': 'Masih di luar',
        'Approved permit': 'Permit diluluskan',
        'Last updated:': 'Kemas kini terakhir:',
        'now': 'sekarang',
        'sync pending': 'menunggu segerak',
        'Previous day': 'Hari sebelumnya',
        'Next day': 'Hari seterusnya',
        'Search name, ID or course': 'Cari nama, ID atau kursus',
        'Search the table': 'Cari dalam jadual',
        'Activity': 'Aktiviti',
        'Course': 'Kursus',
        'Status': 'Status',
        'Checked in late': 'Daftar masuk lewat',
        'Checked in on time': 'Daftar masuk tepat masa',
        'Checked out after arriving late': 'Daftar keluar selepas kembali lewat',
        'Checked out on time': 'Daftar keluar tepat masa',
        'Student is currently checked out': 'Pelajar sedang di luar',
        'No records found for this date.': 'Tiada rekod untuk tarikh ini.',
        'No late students on this date.': 'Tiada pelajar lewat pada tarikh ini.',
        'No students match your search.': 'Tiada pelajar sepadan dengan carian anda.',
        'Student Information': 'Maklumat Pelajar',
        'IC Number': 'No. Kad Pengenalan',
        'Address': 'Alamat',
        'Phone Number': 'No. Telefon',
        'Parent/Guardian': 'Ibu Bapa/Penjaga',
        'Student not found.': 'Pelajar tidak dijumpai.',

        // Manage students
        'Records': 'Rekod',
        'Manage Students': 'Urus Pelajar',
        'Add New Student': 'Tambah Pelajar Baharu',
        'Student List': 'Senarai Pelajar',
        'Filter by presence': 'Tapis mengikut kehadiran',
        'All': 'Semua',
        'Suspended': 'Digantung',
        'Search name, ID, course': 'Cari nama, ID, kursus',
        'Search students': 'Cari pelajar',
        'Name': 'Nama',
        'Session': 'Sesi',
        'Late (30 days)': 'Lewat (30 hari)',
        'Presence': 'Kehadiran',
        'Actions': 'Tindakan',
        'until lifted': 'sehingga ditamatkan',
        'lifted': 'ditamatkan',
        'the warden lifts it': 'warden menamatkannya',
        '3 or more late returns in 30 days': '3 kali atau lebih lewat kembali dalam 30 hari',
        'Edit': 'Sunting',
        'Suspend': 'Gantung',
        'Lift suspension': 'Tamatkan gantungan',
        'Delete': 'Padam',
        'No students found': 'Tiada pelajar dijumpai',
        'Add the first student': 'Tambah pelajar pertama',
        'No students match this filter.': 'Tiada pelajar sepadan dengan tapisan ini.',

        // Edit / add / delete student
        'Back to students': 'Kembali ke senarai pelajar',
        'Update the details below, then save.': 'Kemas kini butiran di bawah, kemudian simpan.',
        'Late returns in the last 30 days:': 'Lewat kembali dalam 30 hari lepas:',
        'Suspension': 'Penggantungan',
        'Lift suspension now': 'Tamatkan gantungan sekarang',
        'Reason': 'Sebab',
        'e.g. Late return 3 times this month': 'cth. Lewat kembali 3 kali bulan ini',
        'Length': 'Tempoh',
        'Until a date...': 'Sehingga tarikh...',
        'Until I lift it': 'Sehingga saya tamatkan',
        'Suspended up to and including': 'Digantung sehingga dan termasuk',
        'Suspend student': 'Gantung pelajar',
        "The student can't check out or apply for home leave while suspended, and gets a suspension letter by email.": 'Pelajar tidak boleh daftar keluar atau memohon cuti pulang semasa digantung, dan akan menerima surat penggantungan melalui e-mel.',
        'Suspension history': 'Sejarah penggantungan',
        'Active': 'Aktif',
        'Update Student': 'Kemas Kini Pelajar',
        'Student details': 'Butiran pelajar',
        'Identification': 'Pengenalan diri',
        'Contact': 'Hubungan',
        'Photo': 'Foto',
        'Click the box, then tap the card on the USB reader.': 'Klik kotak ini, kemudian ketik kad pada pengimbas USB.',
        'Matric ID': 'No. Matrik',
        'RFID UID': 'RFID UID',
        'TVETMARA E-MAIL': 'E-MEL TVETMARA',
        'Parent/Guardian Contact': 'No. Telefon Ibu Bapa/Penjaga',
        'Profile Picture': 'Gambar Profil',
        'Full Name': 'Nama Penuh',
        'Session (e.g., JUL-DIS 2024)': 'Sesi (cth. JUL-DIS 2024)',
        'Matric ID (e.g., 1234567890)': 'No. Matrik (cth. 1234567890)',
        'RFID UID (Tap your IC on RFID scanner)': 'RFID UID (Ketik kad pengenalan pada pengimbas RFID)',
        'TVETMARA Email (e.g., student@sgpetani.tvetmara.edu.my)': 'E-mel TVETMARA (cth. student@sgpetani.tvetmara.edu.my)',
        'TVETMARA Email': 'E-mel TVETMARA',
        'Currently:': 'Semasa:',
        'Clear': 'Kosongkan',
        'Change:': 'Tukar:',
        'This field is required.': 'Ruangan ini wajib diisi.',
        'Enter a valid email address.': 'Masukkan alamat e-mel yang sah.',
        'Email me notifications': 'Hantar notifikasi kepada saya melalui e-mel',
        'Send new home leave requests and late returns to the email above.': 'Hantar permohonan cuti pulang baharu dan kelewatan kembali ke e-mel di atas.',
        'Fields marked': 'Ruangan bertanda',
        'are required.': 'wajib diisi.',
        'Add Student': 'Tambah Pelajar',
        'Form Guide': 'Panduan Borang',
        'Full Name & Course': 'Nama Penuh & Kursus',
        "Enter the student's legal name and official course abbreviation (e.g., Diploma in Computer Science).": 'Masukkan nama sah pelajar dan singkatan kursus rasmi (cth. Diploma Sains Komputer).',
        'Type the intake batch. The box will auto-format to uppercase with dashes (e.g., typing': 'Taip kumpulan pengambilan. Kotak ini akan diformat sendiri kepada huruf besar dengan sengkang (cth. menaip',
        'becomes': 'menjadi',
        'Matric ID & IC Number': 'No. Matrik & No. Kad Pengenalan',
        'Enter the matric & IC number.': 'Masukkan no. matrik & no. kad pengenalan.',
        "Click into the input field and scan the student's IC using the USB reader to capture the chip serial number.": 'Klik pada ruangan input dan imbas kad pengenalan pelajar menggunakan pengimbas USB untuk mendapatkan nombor siri cip.',
        'Enter the official institutional email assigned to the student (e.g.,': 'Masukkan e-mel rasmi institusi yang diberikan kepada pelajar (cth.',
        'Parent Contact': 'Hubungan Ibu Bapa',
        'Provide the active phone number of the parent or legal guardian for emergency or checkout alert tracking.': 'Berikan no. telefon aktif ibu bapa atau penjaga sah untuk kecemasan dan makluman daftar keluar.',
        'Delete Student': 'Padam Pelajar',
        'Warning!': 'Amaran!',
        'Are you sure you want to delete this student?': 'Adakah anda pasti mahu memadam pelajar ini?',
        'This action cannot be undone!': 'Tindakan ini tidak boleh dibatalkan!',
        'Yes, Delete Student': 'Ya, Padam Pelajar',
        'Student added successfully.': 'Pelajar berjaya ditambah.',
        'Student updated successfully.': 'Maklumat pelajar berjaya dikemas kini.',
        'Student deleted successfully.': 'Pelajar berjaya dipadam.',
        'Please give a reason for the suspension.': 'Sila berikan sebab penggantungan.',
        'Please pick a suspension end date from today onwards.': 'Sila pilih tarikh tamat gantungan mulai hari ini.',
        'Please choose how long the suspension lasts.': 'Sila pilih tempoh penggantungan.',

        // Profile
        'Account': 'Akaun',
        'Your photo and contact details.': 'Foto dan butiran hubungan anda.',
        'Phone': 'Telefon',
        'Email': 'E-mel',
        'Edit profile': 'Sunting profil',
        'Save Profile': 'Simpan Profil',
        'Profile updated successfully.': 'Profil berjaya dikemas kini.',

        // Manage / view requests
        'Approvals': 'Kelulusan',
        'Manage Outing Requests': 'Urus Permohonan Outing',
        'Nothing waiting for a decision.': 'Tiada permohonan menunggu keputusan.',
        'selected': 'dipilih',
        'Bulk action': 'Tindakan pukal',
        'Approve Selected': 'Luluskan Yang Dipilih',
        'Reject Selected': 'Tolak Yang Dipilih',
        'Apply Action': 'Laksana Tindakan',
        'Pending Outing Requests': 'Permohonan Outing Belum Diproses',
        'Approve': 'Luluskan',
        'Reject': 'Tolak',
        'View': 'Lihat',
        'View Details': 'Lihat Butiran',
        'New home leave requests from students will show up here.': 'Permohonan cuti pulang baharu daripada pelajar akan dipaparkan di sini.',
        'Confirm Rejection': 'Sahkan Penolakan',
        'Reject the outing request from': 'Tolak permohonan outing daripada',
        'Justification / Reason:': 'Justifikasi / Sebab:',
        'Provide a reason for rejecting this request...': 'Berikan sebab permohonan ini ditolak...',
        'No request selected': 'Tiada permohonan dipilih',
        'Tick at least one request first, then press Apply Action.': 'Tandakan sekurang-kurangnya satu permohonan, kemudian tekan Laksana Tindakan.',
        'Please select at least one request.': 'Sila pilih sekurang-kurangnya satu permohonan.',
        'That request was already decided. No email was sent again.': 'Permohonan itu sudah diputuskan. Tiada e-mel dihantar semula.',
        'You must provide a justification text to reject this request.': 'Anda mesti memberikan justifikasi untuk menolak permohonan ini.',
        '(No email sent.)': '(Tiada e-mel dihantar.)',
        'Back to requests': 'Kembali ke senarai permohonan',
        'Outing Request Details': 'Butiran Permohonan Outing',
        'Student ID': 'ID Pelajar',
        'Outing Details': 'Butiran Outing',
        'Leave': 'Keluar',
        'Return by': 'Kembali sebelum',
        'Type': 'Jenis',
        'Back': 'Kembali',

        // Test form (superuser only)
        'Submit Outing Request': 'Hantar Permohonan Outing',
        'Matric ID / Student ID:': 'No. Matrik / ID Pelajar:',
        'Enter your matric ID': 'Masukkan no. matrik anda',
        'Enter': 'Masuk',
        'Name:': 'Nama:',
        'Course:': 'Kursus:',
        'Session:': 'Sesi:',
        'Request Type:': 'Jenis Permohonan:',
        'Destination:': 'Destinasi:',
        'Purpose:': 'Tujuan:',
        'Date:': 'Tarikh:',
        'Time:': 'Masa:',
        'Return Date:': 'Tarikh Kembali:',
        "You must be back by that day's outing return time.": 'Anda mesti kembali sebelum masa kembali outing hari tersebut.',
        'Submit Request': 'Hantar Permohonan',
        'Error:': 'Ralat:',
        'Student not found': 'Pelajar tidak dijumpai',

        // Page titles (the part before " · ASRAMAku")
        'Edit Student': 'Sunting Pelajar',
        'My Profile': 'Profil Saya',
        'Request details': 'Butiran permohonan'
    };

    // Text with names, dates or numbers in it. $1, $2... are put back in
    // (and are translated too if they are in WORDS). The first match wins.
    var PATTERNS = [
        [/^Welcome (.+)!$/, 'Selamat datang $1!'],
        [/^(\d+) students? registered in the hostel\.$/, '$1 pelajar berdaftar di asrama.'],
        [/^(\d+) requests? waiting for a decision\.$/, '$1 permohonan menunggu keputusan.'],
        [/^(\d+) pending$/, '$1 menunggu'],
        [/^(\d+) days$/, '$1 hari'],
        [/^Viewing: (.+)$/, 'Paparan: $1'],
        [/^Return by (.+)$/, 'Kembali sebelum $1'],
        [/^Return ([A-Z][a-z]{2} \d{2})$/, 'Kembali $1'],
        [/^(\d{2} [A-Z][a-z]{2}) to (\d{2} [A-Z][a-z]{2})$/, '$1 hingga $2'],
        [/^(Home Leave|Outing) \(return by (.+)\)$/, '$1 (kembali sebelum $2)'],
        [/^Requested (.+)$/, 'Dimohon $1'],
        [/^(.+) · requested (.+)$/, '$1 · dimohon $2'],
        [/^Select request from (.+)$/, 'Pilih permohonan daripada $1'],
        [/^Edit Student: (.+)$/, 'Sunting Pelajar: $1'],
        [/^My Profile: (.+)$/, 'Profil Saya: $1'],
        [/^Suspended until (.+)$/, 'Digantung sehingga $1'],
        [/^until (.+)$/, 'sehingga $1'],
        [/^Reason: (.*)$/, 'Sebab: $1'],
        [/^to (.+) \(lifted by (.+)\)$/, 'hingga $1 (ditamatkan oleh $2)'],
        [/^to (.+) \(lifted\)$/, 'hingga $1 (ditamatkan)'],
        [/^to until lifted$/, 'hingga ditamatkan'],
        [/^to (.+)$/, 'hingga $1'],
        [/^(.*) · by (\S+)$/, '$1 · oleh $2'],
        [/^Student with this (.+) already exists\.$/, 'Pelajar dengan $1 ini sudah wujud.'],
        [/^Home leave cannot be longer than (\d+) days\.$/, 'Cuti pulang tidak boleh melebihi $1 hari.'],
        [/^You are suspended from home leave until (.+)\. Reason: (.*)$/, 'Anda digantung daripada cuti pulang sehingga $1. Sebab: $2'],
        [/^(.+) is suspended until (.+)\. Reason: (.*)$/, '$1 digantung sehingga $2. Sebab: $3'],
        [/^(.+) is suspended until (.+)\. Suspension letter emailed\.$/, '$1 digantung sehingga $2. Surat penggantungan telah dihantar melalui e-mel.'],
        [/^(.+) is suspended until (.+)\. \(?No email sent: the student has no email\.\)?$/, '$1 digantung sehingga $2. Tiada e-mel dihantar: pelajar tiada e-mel.'],
        [/^(.+) is already suspended\. Lift that suspension first\.$/, '$1 sudah digantung. Tamatkan gantungan itu dahulu.'],
        [/^(.+) is not suspended\.$/, '$1 tidak digantung.'],
        [/^Suspension on (.+?) (?:has been )?lifted\.$/, 'Gantungan ke atas $1 telah ditamatkan.'],
        [/^(.+) checked out successfully\.$/, '$1 berjaya daftar keluar.'],
        [/^(.+) checked in successfully\.$/, '$1 berjaya daftar masuk.'],
        [/^Late check-in notice: (.+) returned after the (.+) deadline\.$/, 'Notis lewat: $1 kembali selepas had masa $2.'],
        [/^(\d+) request\(s\) (approved|rejected)\. (\d+) already decided, skipped\.$/, '$1 permohonan $2. $3 sudah diputuskan, dilangkau.'],
        [/^(\d+) request\(s\) (approved|rejected)\.$/, '$1 permohonan $2.'],
        [/^Request from (.+?) approved\.( \(No email sent\.\))?$/, 'Permohonan daripada $1 diluluskan.$2'],
        [/^Request from (.+?) rejected\. Reason: (.*?)( \(No email sent\.\))?$/, 'Permohonan daripada $1 ditolak. Sebab: $2$3']
    ];

    var ATTRS = ['placeholder', 'title', 'aria-label', 'data-label', 'data-bs-original-title'];
    var SKIP_TAGS = { SCRIPT: 1, STYLE: 1, NOSCRIPT: 1, TEXTAREA: 1, CODE: 1 };

    var lang = 'en';
    try { if (localStorage.getItem(STORAGE_KEY) === 'ms') lang = 'ms'; } catch (e) {}

    var textDone = new Map();  // text node -> { en, ms }
    var attrDone = new Map();  // element -> { attr: { en, ms } }
    var observer = null;

    // English text -> Malay text, or null when we don't know it. Keeps the spaces around it.
    function toMalay(text) {
        var key = text.replace(/\s+/g, ' ').trim();
        if (!key) return null;
        var out = WORDS[key];
        if (out === undefined) {
            for (var i = 0; i < PATTERNS.length; i++) {
                var m = key.match(PATTERNS[i][0]);
                if (m) {
                    out = PATTERNS[i][1].replace(/\$(\d)/g, function (_, n) {
                        var part = m[n] || '';
                        var t = part.trim() && WORDS[part.trim()];
                        return t ? part.replace(part.trim(), t) : part;
                    });
                    break;
                }
            }
        }
        if (out === undefined) return null;
        return text.match(/^\s*/)[0] + out + text.match(/\s*$/)[0];
    }

    function skipped(node) {
        for (var el = node.parentNode; el && el.nodeType === 1; el = el.parentNode) {
            if (SKIP_TAGS[el.tagName] || el.hasAttribute('data-no-translate')) return true;
            // An <option> with no value uses its text as the value, so leave it alone
            if (el.tagName === 'OPTION' && !el.hasAttribute('value')) return true;
        }
        return false;
    }

    function doText(node) {
        var done = textDone.get(node);
        if (done && node.nodeValue === done.ms) return;
        var parent = node.parentNode;
        if (!parent || skipped(node)) return;
        var en = node.nodeValue;
        var ms;
        if (parent.tagName === 'TITLE') {
            // "Dashboard · ASRAMAku": translate the part before the dot
            var parts = en.split(' · ');
            var first = toMalay(parts[0]);
            ms = first === null ? null : [first].concat(parts.slice(1)).join(' · ');
        } else {
            ms = toMalay(en);
        }
        if (ms === null || ms === en) return;
        textDone.set(node, { en: en, ms: ms });
        node.nodeValue = ms;
    }

    function doAttrs(el) {
        if (el.hasAttribute('data-no-translate') || el.tagName === 'SCRIPT' || el.tagName === 'STYLE') return;
        for (var i = 0; i < ATTRS.length; i++) {
            var name = ATTRS[i];
            var en = el.getAttribute(name);
            if (!en) continue;
            var saved = attrDone.get(el) || {};
            if (saved[name] && saved[name].ms === en) continue;
            var ms = toMalay(en);
            if (ms === null || ms === en) continue;
            saved[name] = { en: en, ms: ms };
            attrDone.set(el, saved);
            el.setAttribute(name, ms);
        }
    }

    function walk(root) {
        if (root.nodeType === 3) { doText(root); return; }
        if (root.nodeType !== 1 && root.nodeType !== 9) return;
        if (root.nodeType === 1) {
            if (skipped(root) || root.hasAttribute('data-no-translate')) return;
            doAttrs(root);
        }
        var els = root.querySelectorAll('*');
        for (var i = 0; i < els.length; i++) doAttrs(els[i]);
        var it = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
        var n;
        while ((n = it.nextNode())) doText(n);
        tidy();
    }

    // Forget nodes that are no longer on the page (the dashboard redraws its table)
    function tidy() {
        if (textDone.size < 3000) return;
        textDone.forEach(function (v, node) { if (!node.isConnected) textDone.delete(node); });
        attrDone.forEach(function (v, el) { if (!el.isConnected) attrDone.delete(el); });
    }

    function onChange(records) {
        for (var i = 0; i < records.length; i++) {
            var r = records[i];
            if (r.type === 'characterData') doText(r.target);
            else if (r.type === 'attributes') doAttrs(r.target);
            else for (var j = 0; j < r.addedNodes.length; j++) walk(r.addedNodes[j]);
        }
    }

    function startWatching() {
        if (observer) return;
        observer = new MutationObserver(onChange);
        observer.observe(document.documentElement, {
            childList: true, subtree: true, characterData: true,
            attributes: true, attributeFilter: ATTRS
        });
    }

    function stopWatching() {
        if (observer) { observer.disconnect(); observer = null; }
    }

    function backToEnglish() {
        textDone.forEach(function (v, node) { if (node.nodeValue === v.ms) node.nodeValue = v.en; });
        attrDone.forEach(function (saved, el) {
            Object.keys(saved).forEach(function (name) {
                if (el.getAttribute(name) === saved[name].ms) el.setAttribute(name, saved[name].en);
            });
        });
        textDone.clear();
        attrDone.clear();
    }

    // The BM / EN buttons show the language you switch TO
    function updateButtons() {
        var toMs = lang === 'en';
        document.querySelectorAll('[data-lang-toggle]').forEach(function (btn) {
            btn.setAttribute('data-no-translate', '');
            var label = toMs ? 'Tukar ke Bahasa Melayu' : 'Switch to English';
            btn.title = label;
            btn.setAttribute('aria-label', label);
            var code = btn.querySelector('[data-lang-label]');
            if (code) code.textContent = toMs ? 'BM' : 'EN';
        });
    }

    function setLang(next) {
        lang = next === 'ms' ? 'ms' : 'en';
        try { localStorage.setItem(STORAGE_KEY, lang); } catch (e) {}
        document.documentElement.lang = lang;
        if (lang === 'ms') {
            walk(document);
            startWatching();
        } else {
            stopWatching();
            backToEnglish();
        }
        updateButtons();
    }

    // Lets other scripts ask which language is showing
    window.asramakuLang = function () { return lang; };

    // Malay picked before: translate while the page is still loading, so English barely shows
    if (lang === 'ms') {
        document.documentElement.lang = 'ms';
        startWatching();
    }

    document.addEventListener('DOMContentLoaded', function () {
        if (lang === 'ms') walk(document);
        updateButtons();
    });

    document.addEventListener('click', function (event) {
        var btn = event.target.closest && event.target.closest('[data-lang-toggle]');
        if (!btn) return;
        event.preventDefault();
        setLang(lang === 'ms' ? 'en' : 'ms');
    });
})();
