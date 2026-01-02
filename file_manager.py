from flask import (
    jsonify, render_template, request,
    send_from_directory, redirect, url_for, send_file
)
from pathlib import Path
import os
import zipfile
import tempfile

def register_file_manager(app, requires_auth, TEMPLAR_ROOT):

    # ---------------------
    # CHUNKED UPLOAD
    # ---------------------
    @app.route("/api/upload_chunk", methods=["POST"])
    @requires_auth
    def upload_chunk():
        file = request.files.get("file")
        filename = request.form.get("filename")
        index = int(request.form.get("index"))
        total = int(request.form.get("total"))

        if not file or not filename:
            return "Missing file or filename", 400

        tmp_dir = TEMPLAR_ROOT / ".upload_tmp"
        tmp_dir.mkdir(exist_ok=True)

        tmp_file = tmp_dir / filename
        mode = "ab" if tmp_file.exists() else "wb"

        with open(tmp_file, mode) as f:
            f.write(file.read())

        if index + 1 == total:
            final_path = TEMPLAR_ROOT / filename
            tmp_file.rename(final_path)

            if final_path.suffix == ".zip":
                with zipfile.ZipFile(final_path, "r") as zip_ref:
                    zip_ref.extractall(TEMPLAR_ROOT)
                final_path.unlink()

        return jsonify(ok=True)

    # ---------------------
    # BROWSE
    # ---------------------
    @app.route("/browse/")
    @app.route("/browse/<path:subpath>")
    @requires_auth
    def browse(subpath=""):
        current = (TEMPLAR_ROOT / subpath).resolve()
        if not current.is_dir() or (TEMPLAR_ROOT not in current.parents and current != TEMPLAR_ROOT):
            return redirect(url_for("browse"))

        dirs, files = [], []
        for item in sorted(current.iterdir()):
            rel = item.relative_to(TEMPLAR_ROOT)
            if item.is_dir():
                dirs.append(rel)
            else:
                files.append(rel)

        all_subfolders = [
            p.relative_to(TEMPLAR_ROOT)
            for p in TEMPLAR_ROOT.rglob("*")
            if p.is_dir()
        ]

        parent = None
        if current != TEMPLAR_ROOT:
            parent = url_for("browse", subpath=str(current.parent.relative_to(TEMPLAR_ROOT)))

        return render_template(
            "browse.html",
            dirs=dirs,
            files=files,
            parent=parent,
            relpath=subpath,
            all_subfolders=all_subfolders
        )

    # ---------------------
    # DOWNLOAD
    # ---------------------
    @app.route("/download/<path:filepath>")
    @requires_auth
    def download(filepath):
        target = (TEMPLAR_ROOT / filepath).resolve()
        if not target.is_file() or TEMPLAR_ROOT not in target.parents:
            return "Invalid path", 404
        return send_from_directory(target.parent, target.name, as_attachment=True)

    # ---------------------
    # ZIP
    # ---------------------
    @app.route("/zip/<path:path>")
    @requires_auth
    def zip_folder(path):
        folder = (TEMPLAR_ROOT / path).resolve()
        if not folder.is_dir() or TEMPLAR_ROOT not in folder.parents:
            return "Invalid folder", 404

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
        with zipfile.ZipFile(tmp.name, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(folder):
                for file in files:
                    full = Path(root) / file
                    zipf.write(full, full.relative_to(folder))

        return send_file(tmp.name, as_attachment=True, download_name=f"{folder.name}.zip")

    # ---------------------
    # CREATE FOLDER
    # ---------------------
    @app.route("/create_folder", methods=["POST"])
    @requires_auth
    def create_folder():
        parent = request.form.get("parent", "")
        foldername = request.form.get("foldername", "").strip()

        target = (TEMPLAR_ROOT / parent / foldername).resolve()
        if TEMPLAR_ROOT not in target.parents:
            return "Invalid path", 400

        target.mkdir()
        return redirect(url_for("browse", subpath=parent))

    # ---------------------
    # RENAME
    # ---------------------
    @app.route("/rename", methods=["POST"])
    @requires_auth
    def rename():
        path = request.form.get("path")
        newname = request.form.get("newname")

        target = (TEMPLAR_ROOT / path).resolve()
        newpath = target.parent / newname

        target.rename(newpath)
        return redirect(url_for("browse", subpath=str(target.parent.relative_to(TEMPLAR_ROOT))))

    # ---------------------
    # DELETE
    # ---------------------
    @app.route("/delete", methods=["POST"])
    @requires_auth
    def delete():
        path = request.form.get("path")
        target = (TEMPLAR_ROOT / path).resolve()

        if target.is_file():
            target.unlink()
        else:
            target.rmdir()

        return redirect(url_for("browse", subpath=str(target.parent.relative_to(TEMPLAR_ROOT))))

    # ---------------------
    # MOVE
    # ---------------------
    @app.route("/move", methods=["POST"])
    @requires_auth
    def move():
        path = request.form.get("path")
        dest_folder = request.form.get("dest")

        target = (TEMPLAR_ROOT / path).resolve()
        dest = (TEMPLAR_ROOT / dest_folder).resolve()

        target.rename(dest / target.name)
        return redirect(url_for("browse", subpath=str(target.parent.relative_to(TEMPLAR_ROOT))))
