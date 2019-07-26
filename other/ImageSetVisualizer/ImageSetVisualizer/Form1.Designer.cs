namespace ImageSetVisualizer
{
    partial class Form1
    {
        /// <summary>
        /// Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        /// Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        /// <summary>
        /// Required method for Designer support - do not modify
        /// the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            this.trkbarPlayback = new System.Windows.Forms.TrackBar();
            this.picboxPicture = new System.Windows.Forms.PictureBox();
            this.lblText = new System.Windows.Forms.Label();
            this.picboxStick = new System.Windows.Forms.PictureBox();
            this.btnRename = new System.Windows.Forms.Button();
            this.btnDelete = new System.Windows.Forms.Button();
            this.plot = new OxyPlot.WindowsForms.PlotView();
            this.lblStickCoords = new System.Windows.Forms.Label();
            ((System.ComponentModel.ISupportInitialize)(this.trkbarPlayback)).BeginInit();
            ((System.ComponentModel.ISupportInitialize)(this.picboxPicture)).BeginInit();
            ((System.ComponentModel.ISupportInitialize)(this.picboxStick)).BeginInit();
            this.SuspendLayout();
            // 
            // trkbarPlayback
            // 
            this.trkbarPlayback.Anchor = ((System.Windows.Forms.AnchorStyles)(((System.Windows.Forms.AnchorStyles.Bottom | System.Windows.Forms.AnchorStyles.Left) 
            | System.Windows.Forms.AnchorStyles.Right)));
            this.trkbarPlayback.Location = new System.Drawing.Point(12, 923);
            this.trkbarPlayback.Name = "trkbarPlayback";
            this.trkbarPlayback.Size = new System.Drawing.Size(1135, 45);
            this.trkbarPlayback.TabIndex = 0;
            this.trkbarPlayback.KeyDown += new System.Windows.Forms.KeyEventHandler(this.TrkbarPlayback_KeyDown);
            this.trkbarPlayback.KeyPress += new System.Windows.Forms.KeyPressEventHandler(this.TrkbarPlayback_KeyPress);
            // 
            // picboxPicture
            // 
            this.picboxPicture.BackColor = System.Drawing.Color.Gray;
            this.picboxPicture.Location = new System.Drawing.Point(12, 12);
            this.picboxPicture.Name = "picboxPicture";
            this.picboxPicture.Size = new System.Drawing.Size(640, 480);
            this.picboxPicture.SizeMode = System.Windows.Forms.PictureBoxSizeMode.Zoom;
            this.picboxPicture.TabIndex = 1;
            this.picboxPicture.TabStop = false;
            // 
            // lblText
            // 
            this.lblText.AutoSize = true;
            this.lblText.Location = new System.Drawing.Point(12, 495);
            this.lblText.Name = "lblText";
            this.lblText.Size = new System.Drawing.Size(35, 13);
            this.lblText.TabIndex = 2;
            this.lblText.Text = "label1";
            // 
            // picboxStick
            // 
            this.picboxStick.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(192)))), ((int)(((byte)(255)))), ((int)(((byte)(192)))));
            this.picboxStick.Location = new System.Drawing.Point(658, 12);
            this.picboxStick.Name = "picboxStick";
            this.picboxStick.Size = new System.Drawing.Size(280, 280);
            this.picboxStick.TabIndex = 3;
            this.picboxStick.TabStop = false;
            this.picboxStick.MouseClick += new System.Windows.Forms.MouseEventHandler(this.PicboxStick_MouseClick);
            this.picboxStick.MouseDown += new System.Windows.Forms.MouseEventHandler(this.PicboxStick_MouseDown);
            this.picboxStick.MouseLeave += new System.EventHandler(this.PicboxStick_MouseLeave);
            this.picboxStick.MouseMove += new System.Windows.Forms.MouseEventHandler(this.PicboxStick_MouseMove);
            this.picboxStick.MouseUp += new System.Windows.Forms.MouseEventHandler(this.PicboxStick_MouseUp);
            // 
            // btnRename
            // 
            this.btnRename.Location = new System.Drawing.Point(944, 12);
            this.btnRename.Name = "btnRename";
            this.btnRename.Size = new System.Drawing.Size(75, 23);
            this.btnRename.TabIndex = 4;
            this.btnRename.Text = "Rename";
            this.btnRename.UseVisualStyleBackColor = true;
            this.btnRename.Click += new System.EventHandler(this.BtnRename_Click);
            this.btnRename.KeyDown += new System.Windows.Forms.KeyEventHandler(this.BtnRename_KeyDown);
            // 
            // btnDelete
            // 
            this.btnDelete.Location = new System.Drawing.Point(944, 41);
            this.btnDelete.Name = "btnDelete";
            this.btnDelete.Size = new System.Drawing.Size(75, 23);
            this.btnDelete.TabIndex = 4;
            this.btnDelete.Text = "Delete";
            this.btnDelete.UseVisualStyleBackColor = true;
            this.btnDelete.Click += new System.EventHandler(this.BtnDelete_Click);
            this.btnDelete.KeyDown += new System.Windows.Forms.KeyEventHandler(this.BtnDelete_KeyDown);
            // 
            // plot
            // 
            this.plot.Anchor = ((System.Windows.Forms.AnchorStyles)((((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Bottom) 
            | System.Windows.Forms.AnchorStyles.Left) 
            | System.Windows.Forms.AnchorStyles.Right)));
            this.plot.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(255)))), ((int)(((byte)(224)))), ((int)(((byte)(192)))));
            this.plot.Location = new System.Drawing.Point(12, 526);
            this.plot.Name = "plot";
            this.plot.PanCursor = System.Windows.Forms.Cursors.Hand;
            this.plot.Size = new System.Drawing.Size(1135, 391);
            this.plot.TabIndex = 5;
            this.plot.ZoomHorizontalCursor = System.Windows.Forms.Cursors.SizeWE;
            this.plot.ZoomRectangleCursor = System.Windows.Forms.Cursors.No;
            this.plot.ZoomVerticalCursor = System.Windows.Forms.Cursors.No;
            this.plot.KeyDown += new System.Windows.Forms.KeyEventHandler(this.Plot_KeyDown);
            // 
            // lblStickCoords
            // 
            this.lblStickCoords.AutoSize = true;
            this.lblStickCoords.Location = new System.Drawing.Point(658, 295);
            this.lblStickCoords.Name = "lblStickCoords";
            this.lblStickCoords.Size = new System.Drawing.Size(35, 13);
            this.lblStickCoords.TabIndex = 6;
            this.lblStickCoords.Text = "label1";
            // 
            // Form1
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(6F, 13F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(1159, 980);
            this.Controls.Add(this.lblStickCoords);
            this.Controls.Add(this.btnDelete);
            this.Controls.Add(this.btnRename);
            this.Controls.Add(this.picboxStick);
            this.Controls.Add(this.lblText);
            this.Controls.Add(this.picboxPicture);
            this.Controls.Add(this.trkbarPlayback);
            this.Controls.Add(this.plot);
            this.Name = "Form1";
            this.Text = "ImageSetVisualizer";
            this.Shown += new System.EventHandler(this.Form1_Shown);
            this.KeyDown += new System.Windows.Forms.KeyEventHandler(this.Form1_KeyDown);
            ((System.ComponentModel.ISupportInitialize)(this.trkbarPlayback)).EndInit();
            ((System.ComponentModel.ISupportInitialize)(this.picboxPicture)).EndInit();
            ((System.ComponentModel.ISupportInitialize)(this.picboxStick)).EndInit();
            this.ResumeLayout(false);
            this.PerformLayout();

        }

        #endregion

        private System.Windows.Forms.TrackBar trkbarPlayback;
        private System.Windows.Forms.PictureBox picboxPicture;
        private System.Windows.Forms.Label lblText;
        private System.Windows.Forms.PictureBox picboxStick;
        private System.Windows.Forms.Button btnRename;
        private System.Windows.Forms.Button btnDelete;
        private OxyPlot.WindowsForms.PlotView plot;
        private System.Windows.Forms.Label lblStickCoords;
    }
}

