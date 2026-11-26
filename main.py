import os, sqlite3
from datetime import datetime
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.core.window import Window
from kivy.metrics import dp

Window.clearcolor = (0.92, 0.94, 0.97, 1)

class WarehouseApp(App):
    def build(self):
        self.db_name = os.path.join(self.user_data_dir, 'warehouse.db')
        self.create_database()
        self.main = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(10))
        Window.softinput_mode = 'pan'
        self.show_home()
        return self.main

    def create_database(self):
        with sqlite3.connect(self.db_name) as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS products (
                code TEXT PRIMARY KEY, name TEXT NOT NULL, category TEXT,
                quantity INTEGER NOT NULL, unit TEXT)''')
            conn.execute('''CREATE TABLE IF NOT EXISTS movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT,
                movement_type TEXT, quantity INTEGER,
                date DATETIME DEFAULT CURRENT_TIMESTAMP)''')

    def clear_screen(self): self.main.clear_widgets()

    def add_title(self, text):
        self.main.add_widget(Label(text=text, font_size=dp(24), bold=True,
            color=(0, .3, .6, 1), size_hint=(1, None), height=dp(60)))

    def add_button(self, text, function, color=(.1, .4, .7, 1)):
        b = Button(text=text, font_size=dp(18), size_hint=(1, None), height=dp(58),
                  background_normal='', background_color=color)
        b.bind(on_press=function); self.main.add_widget(b)

    def add_input(self, hint, numeric=False):
        field = TextInput(hint_text=hint, multiline=False,
            input_filter='int' if numeric else None, size_hint=(1, None),
            height=dp(55), font_size=dp(18), foreground_color=(0,0,0,1),
            background_color=(1,1,1,1), cursor_color=(0,.3,.8,1),
            hint_text_color=(.5,.5,.5,1), padding=[dp(12),dp(15)])
        self.main.add_widget(field); return field

    def make_input(self, hint, numeric=False):
        return TextInput(hint_text=hint, multiline=False,
            input_filter='int' if numeric else None, size_hint=(1,None),
            height=dp(58), font_size=dp(18), foreground_color=(0,0,0,1),
            background_color=(1,1,1,1), cursor_color=(0,.3,.8,1),
            hint_text_color=(.5,.5,.5,1), padding=[dp(12),dp(16)])

    def show_message(self, text):
        self.clear_screen(); self.add_title(text); self.add_button('BACK TO HOME', self.show_home)

    def show_home(self, instance=None):
        self.clear_screen()
        self.main.padding = dp(6)
        self.main.spacing = dp(4)
        self.add_title('WAREHOUSE MANAGEMENT')

        # Single-column menu with button heights adapted to the phone screen.
        items = [
            ('ADD PRODUCT', self.show_add_product),
            ('PRODUCT LIST', self.show_product_list),
            ('STOCK IN', self.show_stock_in),
            ('STOCK OUT', self.show_stock_out),
            ('STOCK MOVEMENTS', self.show_movements),
            ('SEARCH PRODUCT', self.show_search),
            ('REPORTS', self.show_reports),
            ('EXPORT TO EXCEL', self.export_excel),
            ('EXPORT TO PDF', self.export_pdf),
            ('PRINT REPORT', self.export_pdf),
        ]

        # Reserve space for the heading, padding and gaps, then divide
        # the remaining height evenly between the 10 buttons.
        reserved = dp(115)
        gaps = dp(4) * (len(items) - 1)
        button_height = (Window.height - reserved - gaps) / len(items)
        button_height = max(dp(30), min(dp(56), button_height))

        grid = GridLayout(cols=1, spacing=dp(4), padding=dp(2),
                          size_hint=(1, 1), row_force_default=True,
                          row_default_height=button_height)
        for text, function in items:
            button = Button(text=text, font_size=dp(14),
                           size_hint=(1, None), height=button_height,
                           background_normal='',
                           background_color=(.1, .4, .7, 1))
            button.bind(on_press=function)
            grid.add_widget(button)

        self.main.add_widget(grid)

    def show_add_product(self, instance=None):
        self.clear_screen(); self.add_title('ADD NEW PRODUCT')
        scroll=ScrollView(); grid=GridLayout(cols=1,spacing=dp(12),padding=dp(5),size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))
        self.p_code=self.make_input('Product Code'); self.p_name=self.make_input('Product Name')
        self.p_category=self.make_input('Category'); self.p_quantity=self.make_input('Opening Quantity',True)
        self.p_unit=self.make_input('Unit')
        for f in [self.p_code,self.p_name,self.p_category,self.p_quantity,self.p_unit]: grid.add_widget(f)
        scroll.add_widget(grid); self.main.add_widget(scroll)
        self.message=Label(text='',color=(.8,0,0,1),size_hint=(1,None),height=dp(40)); self.main.add_widget(self.message)
        self.add_button('SAVE PRODUCT',self.save_product,(.1,.6,.3,1)); self.add_button('BACK',self.show_home)

    def save_product(self, instance):
        code=self.p_code.text.strip(); name=self.p_name.text.strip(); category=self.p_category.text.strip()
        q=self.p_quantity.text.strip(); unit=self.p_unit.text.strip()
        if not code or not name or not q: self.message.text='Please fill required fields'; return
        try:
            amount=int(q)
            if amount<0: self.message.text='Invalid quantity'; return
            with sqlite3.connect(self.db_name) as conn:
                conn.execute('INSERT INTO products VALUES (?,?,?,?,?)',(code,name,category,amount,unit))
                if amount>0: conn.execute('INSERT INTO movements (code,movement_type,quantity) VALUES (?,?,?)',(code,'OPENING',amount))
            self.show_message('PRODUCT SAVED SUCCESSFULLY')
        except sqlite3.IntegrityError: self.message.text='Product Code Already Exists'
        except ValueError: self.message.text='Invalid quantity'

    def create_table(self, headers, rows, widths):
        scroll=ScrollView(do_scroll_x=True,do_scroll_y=True)
        grid=GridLayout(cols=1,spacing=dp(3),size_hint=(None,None),padding=dp(4),width=sum(widths))
        grid.bind(minimum_height=grid.setter('height'))
        def row(values, header=False):
            r=GridLayout(cols=len(headers),size_hint=(None,None),height=dp(55),width=sum(widths))
            for i,val in enumerate(values):
                l=Label(text=str(val),font_size=dp(13),bold=header,
                    color=(0,.3,.6,1) if header else (0,0,0,1),size_hint=(None,1),width=widths[i],halign='center',valign='middle')
                l.bind(size=lambda obj,size:setattr(obj,'text_size',size)); r.add_widget(l)
            grid.add_widget(r)
        row(headers,True)
        if rows:
            for item in rows: row(item)
        else: row(['NO DATA']+['']*(len(headers)-1))
        scroll.add_widget(grid); self.main.add_widget(scroll)

    def show_product_list(self, instance=None):
        self.clear_screen(); self.add_title('PRODUCT LIST')
        with sqlite3.connect(self.db_name) as conn:
            rows=conn.execute('SELECT code,name,category,quantity,unit FROM products ORDER BY name').fetchall()
        self.create_table(['CODE','NAME','CATEGORY','QUANTITY','UNIT'],rows,[dp(110),dp(160),dp(140),dp(120),dp(100)])
        self.add_button('BACK',self.show_home)

    def show_stock_in(self, instance=None): self.show_stock_page('STOCK IN')
    def show_stock_out(self, instance=None): self.show_stock_page('STOCK OUT')

    def show_stock_page(self, movement):
        self.clear_screen(); self.add_title(movement)
        self.stock_code=self.add_input('Product Code'); self.stock_quantity=self.add_input('Quantity',True)
        self.stock_message=Label(text='',color=(.8,0,0,1),size_hint=(1,None),height=dp(50)); self.main.add_widget(self.stock_message)
        self.add_button('CONFIRM',lambda x:self.process_stock(movement),(.1,.6,.3,1)); self.add_button('BACK',self.show_home)

    def process_stock(self, movement):
        code=self.stock_code.text.strip(); q=self.stock_quantity.text.strip()
        if not code or not q: self.stock_message.text='Fill all fields'; return
        try: amount=int(q)
        except ValueError: self.stock_message.text='Invalid quantity'; return
        if amount<=0: self.stock_message.text='Quantity must be positive'; return
        with sqlite3.connect(self.db_name) as conn:
            cur=conn.cursor(); cur.execute('SELECT quantity FROM products WHERE code=?',(code,)); product=cur.fetchone()
            if product is None: self.stock_message.text='Product Not Found'; return
            current=product[0]
            if movement=='STOCK OUT' and amount>current: self.stock_message.text='Insufficient Stock'; return
            new=current+amount if movement=='STOCK IN' else current-amount
            typ='IN' if movement=='STOCK IN' else 'OUT'
            cur.execute('UPDATE products SET quantity=? WHERE code=?',(new,code))
            cur.execute('INSERT INTO movements (code,movement_type,quantity) VALUES (?,?,?)',(code,typ,amount))
        self.stock_message.text='Operation Successful'

    def show_movements(self, instance=None):
        self.clear_screen(); self.add_title('STOCK MOVEMENTS')
        with sqlite3.connect(self.db_name) as conn:
            rows=conn.execute('SELECT id,code,movement_type,quantity,date FROM movements ORDER BY id DESC').fetchall()
        self.create_table(['ID','CODE','TYPE','QUANTITY','DATE'],rows,[dp(65),dp(110),dp(110),dp(110),dp(190)])
        self.add_button('BACK',self.show_home)

    def show_search(self, instance=None):
        self.clear_screen(); self.add_title('SEARCH PRODUCT'); self.search_code=self.add_input('Product Code')
        self.search_result=Label(text='',color=(0,0,0,1),font_size=dp(17),size_hint=(1,None),height=dp(180))
        self.add_button('SEARCH',self.search_product); self.main.add_widget(self.search_result); self.add_button('BACK',self.show_home)

    def search_product(self, instance):
        code=self.search_code.text.strip()
        with sqlite3.connect(self.db_name) as conn: product=conn.execute('SELECT * FROM products WHERE code=?',(code,)).fetchone()
        if product:
            self.search_result.text=(f'PRODUCT FOUND\nCode: {product[0]}\nName: {product[1]}\nCategory: {product[2]}\nQuantity: {product[3]}\nUnit: {product[4]}')
        else: self.search_result.text='PRODUCT NOT FOUND'

    def report_totals(self):
        with sqlite3.connect(self.db_name) as conn:
            total_products=conn.execute('SELECT COUNT(*) FROM products').fetchone()[0]
            total_stock=conn.execute('SELECT COALESCE(SUM(quantity),0) FROM products').fetchone()[0]
            total_in=conn.execute("SELECT COALESCE(SUM(quantity),0) FROM movements WHERE movement_type='IN'").fetchone()[0]
            total_out=conn.execute("SELECT COALESCE(SUM(quantity),0) FROM movements WHERE movement_type='OUT'").fetchone()[0]
        return total_products,total_stock,total_in,total_out

    def show_reports(self, instance=None):
        self.clear_screen(); self.add_title('WAREHOUSE REPORTS')
        a,b,c,d=self.report_totals()
        self.main.add_widget(Label(text=f'TOTAL PRODUCTS: {a}\n\nTOTAL STOCK: {b}\n\nTOTAL STOCK IN: {c}\n\nTOTAL STOCK OUT: {d}',font_size=dp(20),color=(0,.3,.6,1)))
        self.add_button('BACK',self.show_home)

    def export_excel(self, instance=None):
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Font, PatternFill, Alignment
            filename=os.path.join(self.user_data_dir,'Warehouse_Report.xlsx')
            wb=Workbook(); ws=wb.active; ws.title='Products'
            ws.append(['Code','Name','Category','Quantity','Unit'])
            with sqlite3.connect(self.db_name) as conn:
                for row in conn.execute('SELECT code,name,category,quantity,unit FROM products ORDER BY name'): ws.append(list(row))
                moves=wb.create_sheet('Movements'); moves.append(['ID','Code','Type','Quantity','Date'])
                for row in conn.execute('SELECT id,code,movement_type,quantity,date FROM movements ORDER BY id DESC'): moves.append(list(row))
            for sheet in wb.worksheets:
                sheet.freeze_panes='A2'
                for cell in sheet[1]:
                    cell.font=Font(bold=True,color='FFFFFF'); cell.fill=PatternFill('solid',fgColor='1A6699'); cell.alignment=Alignment(horizontal='center')
                for col in sheet.columns:
                    sheet.column_dimensions[col[0].column_letter].width=min(max(len(str(c.value or '')) for c in col)+3,35)
            wb.save(filename); self.show_message('EXCEL FILE SAVED\n'+filename)
        except ImportError: self.show_message('Install openpyxl to export Excel')
        except Exception as e: self.show_message('Excel export error: '+str(e))

    def export_pdf(self, instance=None):
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.platypus import SimpleDocTemplate,Table,TableStyle,Paragraph,Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            filename=os.path.join(self.user_data_dir,'Warehouse_Report.pdf')
            doc=SimpleDocTemplate(filename,pagesize=landscape(A4)); styles=getSampleStyleSheet(); content=[]
            content.append(Paragraph('Warehouse Management Report',styles['Title']))
            content.append(Paragraph('Created: '+datetime.now().strftime('%Y-%m-%d %H:%M'),styles['Normal'])); content.append(Spacer(1,12))
            totals=self.report_totals()
            summary=[['Total Products','Current Stock','Stock In','Stock Out'],list(totals)]
            t=Table(summary,repeatRows=1); t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#1A6699')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('GRID',(0,0),(-1,-1),.5,colors.grey),('ALIGN',(0,0),(-1,-1),'CENTER'),('PADDING',(0,0),(-1,-1),7)])); content.append(t); content.append(Spacer(1,16))
            content.append(Paragraph('Product List',styles['Heading2']))
            with sqlite3.connect(self.db_name) as conn:
                products=conn.execute('SELECT code,name,category,quantity,unit FROM products ORDER BY name').fetchall()
            data=[['Code','Name','Category','Quantity','Unit']]+[list(r) for r in products]
            table=Table(data,repeatRows=1); table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#1A6699')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('GRID',(0,0),(-1,-1),.5,colors.grey),('ALIGN',(0,0),(-1,-1),'CENTER'),('PADDING',(0,0),(-1,-1),5)])); content.append(table)
            doc.build(content); self.show_message('PDF FILE SAVED\n'+filename)
        except ImportError: self.show_message('Install reportlab to export PDF')
        except Exception as e: self.show_message('PDF export error: '+str(e))

WarehouseApp().run()
