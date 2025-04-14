import streamlit as st
def acknowlegments():
    # footer_content = "Developers: <br><br>Leandro Alvarez alvarezleandro720@gmail.com<br>Kristian Vazquez kristian120304@gmail.com<br>Miguel Garcia miguelgarcia2002117@gmail.com <br> Jesus Valdes jesuslvaldes29@gmail.com"
    footer_html = """
        <style>
        .footer {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background-color: rgba(0, 0, 0, 0.7);
            color: white;
            padding: 5px;
            text-align: center;
            z-index: 1000;
            font-size: 0.85em;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            max-height: 20px;
            overflow: hidden;
            transition: max-height 0.3s ease-out;
        }
        
        .footer:hover {
            max-height: 100px;
            overflow-y: auto;
        }
        
        .footer-title {
            cursor: pointer;
            font-weight: bold;
        }
        
        .footer-content {
            margin-top: 5px;
            display: flex;
            flex-direction: column;
            gap: 3px;
        }
        
        .footer::-webkit-scrollbar {
            width: 4px;
        }
        
        .footer::-webkit-scrollbar-track {
            background: transparent;
        }
        
        .footer::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.3);
            border-radius: 4px;
        }
        </style>
        
        <div class="footer">
            <div class="footer-title">Developers</div>
            <div class="footer-content">
                <p>Leandro Alvarez alvarezleandro720@gmail.com</p>
                <p>Kristian Vazquez kristian12034@gmail.com</p>
                <p>Miguel García miguelgarcia2002117@gmail.com</p>
                <p>Jesus Valdes jesusvaldess29@gmail.com</p>
            </div>
        </div>
        """
    st.markdown(footer_html, unsafe_allow_html=True)
