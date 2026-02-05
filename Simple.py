import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3, os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

DB = "presupuestos.db"
os.makedirs("C:/MegaMauri/Programación/PYTHON/Python_Pruebas/facturas", exist_ok=True)

# ================= DB =================
def conectar():
    return sqlite3.connect(DB)

def crear_tablas():
    con = conectar()
    cur = con.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS clientes(
        nombre TEXT PRIMARY KEY,
        direccion TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS productos(
        nombre TEXT PRIMARY KEY,
        precio REAL,
        descuento REAL,
        bulto INTEGER
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS medios_pago(
        nombre TEXT PRIMARY KEY,
        descuento REAL
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS pedidos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente TEXT,
        medio_pago TEXT,
        desc_mp REAL,
        total REAL,
        fecha TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS detalle(
        pedido_id INTEGER,
        producto TEXT,
        precio REAL,
        cantidad INTEGER,
        descuento REAL,
        subtotal REAL
    )""")

    con.commit()
    con.close()

crear_tablas()

# ================= APP =================
class App:
    def __init__(self, root):
        self.root = root
        root.title("Simple")

        self.carrito = []
        self.cliente_actual = None

        # 🔍 BUSQUEDA
        self.productos = []
        self.var_buscar = tk.StringVar()

        barra = tk.Menu(root)
        root.config(menu=barra)
        barra.add_command(label="Clientes", command=self.crud_clientes)
        barra.add_command(label="Productos", command=self.crud_productos)
        barra.add_command(label="Medios de Pago", command=self.crud_medios)
        barra.add_command(label="Historial", command=self.historial)

        top = ttk.Frame(root)
        top.pack(fill="x", pady=5)

        ttk.Button(top, text="Seleccionar cliente", command=self.seleccionar_cliente).pack(side="left", padx=5)

        self.lbl_cliente = ttk.Label(top, text="Cliente:", font=("Arial",10,"bold"))
        self.lbl_cliente.pack(side="left", padx=10)

        self.btn_carrito = ttk.Button(top, text="🛒 0", command=self.ver_carrito)
        self.btn_carrito.pack(side="right", padx=10)

        # 🔍 BUSCADOR
        busq = ttk.Frame(root)
        busq.pack(fill="x", padx=5)

        ttk.Label(busq, text="Buscar producto:").pack(side="left")
        ent_buscar = ttk.Entry(busq, textvariable=self.var_buscar)
        ent_buscar.pack(side="left", fill="x", expand=True, padx=5)
        ent_buscar.bind("<KeyRelease>", self.filtrar_productos)

        # 📊 TABLA PRODUCTOS
        cols = ("Nombre","Precio","Desc %","Bulto")
        self.tv = ttk.Treeview(root, columns=cols, show="headings")
        for c in cols:
            self.tv.heading(c,text=c)
            self.tv.column(c, anchor="center")
        self.tv.pack(fill="both", expand=True)

        self.tv.bind("<Double-1>", self.popup_producto)
        self.cargar_productos()

    # ================= BUSQUEDA =================
    def filtrar_productos(self, event=None):
        texto = self.var_buscar.get().lower()
        self.tv.delete(*self.tv.get_children())
        for p in self.productos:
            if texto in p[0].lower():
                self.tv.insert("", "end", values=p)

    # ================= CLIENTES =================
    def seleccionar_cliente(self):
        w = tk.Toplevel(self.root)
        w.title("Seleccionar cliente")

        t = ttk.Treeview(w, columns=("Nombre","Dirección"), show="headings")
        t.heading("Nombre", text="Nombre")
        t.heading("Dirección", text="Dirección")
        t.pack(fill="both", expand=True)

        con = conectar()
        for r in con.execute("SELECT nombre,direccion FROM clientes"):
            t.insert("", "end", values=r)
        con.close()

        t.bind("<Double-1>", lambda e: self._set_cliente(t, w))

    def _set_cliente(self, t, w):
        item = t.item(t.focus())["values"]
        if item:
            self.cliente_actual = item[0]
            self.lbl_cliente.config(text=f"Cliente: {item[0]}")
            w.destroy()

    # ================= PRODUCTOS =================
    def cargar_productos(self):
        self.tv.delete(*self.tv.get_children())
        self.productos.clear()
        con = conectar()
        for r in con.execute("SELECT nombre,precio,descuento,bulto FROM productos"):
            self.productos.append(r)
            self.tv.insert("", "end", values=r)
        con.close()

    def popup_producto(self, e):
        vals = self.tv.item(self.tv.focus())["values"]
        if not vals: return

        nombre, precio, desc, bulto = vals
        precio, desc, bulto = float(precio), float(desc), int(bulto)

        w = tk.Toplevel()
        w.title(nombre)

        ttk.Label(w,text=f"Precio unitario: $ {precio:.2f}").pack()
        ttk.Label(w,text=f"Descuento: {desc}% desde {bulto}").pack()

        ent = ttk.Entry(w)
        ent.pack()
        ent.focus()

        def ok(event=None):
            c = int(ent.get())
            d = desc if c >= bulto else 0
            sub = precio * c * (1 - d/100)
            self.carrito.append([nombre,precio,c,d,sub])
            self.btn_carrito.config(text=f"🛒 {len(self.carrito)}")
            w.destroy()

        ent.bind("<Return>", ok)
        ttk.Button(w,text="Agregar",command=ok).pack()

    # ================= CARRITO =================
    def ver_carrito(self):
        w = tk.Toplevel()
        w.title("Carrito")

        ttk.Label(w,text=f"Cliente: {self.cliente_actual or 'No seleccionado'}",
                  font=("Arial",10,"bold")).pack()

        cols=("Cant","Producto","Unitario","Desc","Subtotal")
        t=ttk.Treeview(w,columns=cols,show="headings")
        for c in cols: t.heading(c,text=c)
        t.pack(fill="both",expand=True)

        for i,p in enumerate(self.carrito):
            t.insert("", "end", iid=i,
                     values=(p[2],p[0],p[1],f"{p[3]}%",round(p[4],2)))

        def editar(e):
            iid=t.focus()
            if iid=="": return
            it=self.carrito[int(iid)]

            we=tk.Toplevel(w)
            ent=tk.Entry(we)
            ent.insert(0,it[2])
            ent.pack(); ent.focus()

            def ok(event=None):
                c=int(ent.get())
                it[2]=c
                it[4]=it[1]*c*(1-it[3]/100)
                we.destroy()
                w.destroy()
                self.ver_carrito()

            ent.bind("<Return>", ok)
            ttk.Button(we,text="Guardar",command=ok).pack()

        t.bind("<Double-1>", editar)

        ttk.Button(w,text="Eliminar ítem",
                   command=lambda:self._del_item(t,w)).pack(side="left")
        ttk.Button(w,text="Facturar",command=self.facturar).pack(side="right")

    def _del_item(self,t,w):
        iid=t.focus()
        if iid!="":
            del self.carrito[int(iid)]
            self.btn_carrito.config(text=f"🛒 {len(self.carrito)}")
            w.destroy()
            self.ver_carrito()

    # ================= FACTURAR =================
    def facturar(self):
        if not self.cliente_actual:
            messagebox.showerror("Error","Seleccione cliente")
            return

        w=tk.Toplevel()
        con=conectar()
        medios=con.execute("SELECT nombre,descuento FROM medios_pago").fetchall()
        con.close()

        cb=ttk.Combobox(w,values=[m[0] for m in medios])
        cb.pack()

        def ok():
            mp=cb.get()
            dmp=next((m[1] for m in medios if m[0]==mp),0)
            total=sum(p[4] for p in self.carrito)*(1-dmp/100)
            self.guardar_factura(mp,dmp,total)
            w.destroy()

        ttk.Button(w,text="Confirmar",command=ok).pack()

    def guardar_factura(self, mp, dmp, total):
        con=conectar()
        cur=con.cursor()

        cur.execute("""
        INSERT INTO pedidos(cliente,medio_pago,desc_mp,total,fecha)
        VALUES (?,?,?,?,?)
        """,(self.cliente_actual,mp,dmp,total,
             datetime.now().strftime("%d/%m/%Y %H:%M")))

        pid=cur.lastrowid

        for p in self.carrito:
            cur.execute("INSERT INTO detalle VALUES (?,?,?,?,?,?)",
                        (pid,p[0],p[1],p[2],p[3],p[4]))

        con.commit(); con.close()
        self.carrito.clear()
        self.btn_carrito.config(text="🛒 0")
        self.pdf(pid)

    # ================= PDF =================
    def pdf(self, pid):
        from reportlab.lib.units import cm
        from reportlab.lib import colors

        con = conectar()
        ped = con.execute("""
        SELECT cliente, medio_pago, desc_mp, total, fecha
        FROM pedidos WHERE id=?
        """,(pid,)).fetchone()

        det = con.execute("""
        SELECT cantidad, producto, precio, descuento, subtotal
        FROM detalle
        WHERE pedido_id=?
        """,(pid,)).fetchall()
        con.close()

        path = f"C:/MegaMauri/Programación/PYTHON/Python_Pruebas/facturas/factura_{pid}.pdf"
        c = canvas.Canvas(path, pagesize=A4)
        width, height = A4

        X_TOTAL = width - 2*cm

    # ================= COLORES =================
        AZUL = colors.HexColor("#1f4fd8")
        GRIS = colors.HexColor("#555555")
        GRIS_CLARO = colors.HexColor("#cccccc")

    # ================= LOGO =================
        logo = "logo.png"   # opcional
        if os.path.exists(logo):
            c.drawImage(logo, 2*cm, height-3.2*cm, width=4*cm, preserveAspectRatio=True)

    # ================= ENCABEZADO =================
        c.setFont("Helvetica-Bold", 18)
        c.setFillColor(AZUL)
        c.drawRightString(X_TOTAL, height-2*cm, "FACTURA")

        c.setFont("Helvetica", 10)
        c.setFillColor(GRIS)
        c.drawRightString(X_TOTAL, height-2.7*cm, f"N° {pid}")
        c.drawRightString(X_TOTAL, height-3.3*cm, f"Fecha: {ped[4]}")

        c.setFont("Helvetica-Bold", 14)
        c.drawString(2*cm, height-2.2*cm, "MI EMPRESA S.A.")

        c.setFont("Helvetica", 10)
        c.drawString(2*cm, height-3*cm, "CUIT: 30-12345678-9")
        c.drawString(2*cm, height-3.6*cm, "Dirección comercial")

    # ================= CLIENTE =================
        c.setStrokeColor(GRIS_CLARO)
        c.line(2*cm, height-4.2*cm, X_TOTAL, height-4.2*cm)

        c.setFont("Helvetica", 11)
        c.setFillColor(colors.black)
        c.drawString(2*cm, height-5.1*cm, f"Cliente: {ped[0]}")
        c.drawString(2*cm, height-5.8*cm, f"Forma de pago: {ped[1]}")

    # ================= TABLA =================
        y = height-7.3*cm

    # Encabezado fondo
        c.setFillColor(colors.whitesmoke)
        c.rect(2*cm, y-0.5*cm, X_TOTAL-2*cm, 0.8*cm, fill=1, stroke=0)

        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 11)

        c.drawString(2.2*cm, y, "Cant.")
        c.drawString(4*cm, y, "Producto")
        c.drawRightString(12.5*cm, y, "Unit.")
        c.drawRightString(14.5*cm, y, "Desc.")
        c.drawRightString(X_TOTAL, y, "Subtotal")

    # Líneas verticales
        c.setStrokeColor(GRIS_CLARO)
        for x in (3.5*cm, 11.5*cm, 13.5*cm, 15.5*cm):
            c.line(x, y+0.3*cm, x, y-0.5*cm)

        c.line(2*cm, y-0.5*cm, X_TOTAL, y-0.5*cm)

    # ================= DETALLE =================
        c.setFont("Helvetica", 11)
        y -= 1.2*cm
        total_bruto = 0

        for cant, prod, precio, desc, sub in det:
            c.drawString(2.4*cm, y, str(cant))
            c.drawString(4*cm, y, prod)
            c.drawRightString(12.5*cm, y, f"$ {precio:.2f}")
            c.drawRightString(14.5*cm, y, f"{desc}%")
            c.drawRightString(X_TOTAL, y, f"$ {sub:.2f}")
            c.line(2*cm, y-0.4*cm, X_TOTAL, y-0.4*cm)

            total_bruto += sub
            y -= 0.9*cm

    # ================= DESCUENTO POR PAGO =================
        if ped[2] > 0:
            desc_importe = total_bruto * ped[2] / 100

            y -= 0.6*cm
            c.setFont("Helvetica", 11)
            c.drawRightString(
            X_TOTAL,
            y,
            f"Descuento por pago ({ped[2]}%): -$ {desc_importe:.2f}"
            )
            y -= 1*cm

    # ================= TOTAL =================
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(AZUL)
        c.drawRightString(X_TOTAL, y, f"TOTAL: $ {ped[3]:.2f}")

    # ================= PIE =================
        c.setFont("Helvetica-Oblique", 9)
        c.setFillColor(GRIS)
        c.drawCentredString(width/2, 1.5*cm, "Gracias por su compra")

        c.save()
        os.startfile(path)

    # ================= CRUD =================
    def crud(self, tabla, campos):
        w=tk.Toplevel()
        t=ttk.Treeview(w,columns=campos,show="headings")
        for c in campos: t.heading(c,text=c)
        t.pack(fill="both",expand=True)

        def cargar():
            t.delete(*t.get_children())
            con=conectar()
            for r in con.execute(f"SELECT {','.join(campos)} FROM {tabla}"):
                t.insert("", "end", values=r)
            con.close()

        cargar()

        def form(val=None):
            f=tk.Toplevel(w)
            ents={}
            for i,c in enumerate(campos):
                ttk.Label(f,text=c).pack()
                e=ttk.Entry(f); e.pack()
                if val: e.insert(0,val[i])
                ents[c]=e

            def guardar():
                vals=[ents[c].get() for c in campos]
                con=conectar()
                if val:
                    con.execute(
                        f"UPDATE {tabla} SET {','.join(c+'=?' for c in campos)} WHERE {campos[0]}=?",
                        vals+[val[0]])
                else:
                    con.execute(
                        f"INSERT INTO {tabla} VALUES ({','.join('?'*len(campos))})",
                        vals)
                con.commit(); con.close()
                f.destroy(); cargar()

            ttk.Button(f,text="Guardar",command=guardar).pack()

        t.bind("<Double-1>", lambda e: form(t.item(t.focus())["values"]))
        ttk.Button(w,text="Agregar",command=lambda:form()).pack(side="left")
        ttk.Button(w,text="Borrar",
                   command=lambda:self._borrar(tabla,campos,t,cargar)).pack(side="left")

    def _borrar(self,tabla,campos,t,cargar):
        v=t.item(t.focus())["values"]
        if not v: return
        if messagebox.askyesno("Confirmar","Eliminar registro?"):
            con=conectar()
            con.execute(f"DELETE FROM {tabla} WHERE {campos[0]}=?",(v[0],))
            con.commit(); con.close()
            cargar()

    def crud_clientes(self): self.crud("clientes",("nombre","direccion"))
    def crud_productos(self): self.crud("productos",("nombre","precio","descuento","bulto"))
    def crud_medios(self): self.crud("medios_pago",("nombre","descuento"))

    # ================= HISTORIAL =================
    def historial(self):
        w=tk.Toplevel()
        t=ttk.Treeview(w,columns=("Cliente","Total","Fecha"),show="headings")
        for c in ("Cliente","Total","Fecha"): t.heading(c,text=c)
        t.pack(fill="both",expand=True)

        con=conectar()
        for r in con.execute("SELECT id,cliente,total,fecha FROM pedidos"):
            t.insert("", "end", iid=r[0], values=r[1:])
        con.close()

        t.bind("<Double-1>",
               lambda e: os.startfile(
                   f"C:/MegaMauri/Programación/PYTHON/Python_Pruebas/facturas/factura_{t.focus()}.pdf"))

# ================= RUN =================
root=tk.Tk()
App(root)
root.mainloop()
