if uploaded_file is not None:
    # Zgłaszamy systemowi, że plik jest wgrany, aby schować instrukcję przy następnym przeładowaniu
    if not plik_wgrany:
        st.session_state["file_uploaded"] = True
        st.rerun()
        
    try:
        # --- INTELIGENTNE WCZYTYWANIE PLIKU ---
        if uploaded_file.name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(uploaded_file)
        else:
            # Silnik 'python' z sep=None automatycznie wykryje czy separator to przecinek, czy średnik
            df = pd.read_csv(uploaded_file, sep=None, engine='python')
        
        # Jeśli na samej górze są jakieś śmieci/metadane, szukamy wiersza, który wygląda jak właściwy nagłówek
        # Usuwamy puste kolumny i wiersze widma
        df = df.dropna(how='all')
        
        # Jeśli pierwsza kolumna ma nazwę nienumeryczną lub dziwną, a wiersz niżej są poprawne nazwy,
        # program próbuje przesunąć nagłówek (zabezpieczenie przed dodatkowymi opisami nad tabelą)
        if df.shape[0] > 0 and any(df.iloc[0].astype(str).str.contains('lp|id|cena', case=False, na=False)):
            new_header = df.iloc[0]
            df = df[1:]
            df.columns = new_header
            
        # -----------------------------------------------------
        
        # --- AUTOMATYCZNE CZYSZCZENIE DANYCH Z TEKSTU ---
