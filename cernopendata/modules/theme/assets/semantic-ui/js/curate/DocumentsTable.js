import React, { useState, useEffect } from "react";
import { Table, Button, Icon, Pagination } from "semantic-ui-react";
import AddDocumentModal from "./documents/AddDocumentModal";
import EditDocumentModal from "./documents/EditDocumentModal";
import UploadImagesModal from "./documents/UploadImagesModal";
import EditImageModal from "./documents/EditImageModal";
import PreviewImageModal from "./documents/PreviewImageModal";
import usePagination from "./shared/usePagination";
import RowActions from "./shared/RowActions";

export default function DocumentsTable({
  experiment,
  releaseId,
  initialDocuments = [],
  editDisabled = false,
  viewDisabled = false,
}) {
  const [documents, setDocuments] = useState(initialDocuments);
  const [editingDoc, setEditingDoc] = useState(null);

  const pageSize = 5;
  const { page, setPage, visible, totalPages } = usePagination(
    documents,
    pageSize,
  );

  const [addModalOpen, setAddModalOpen] = useState(false);

  const [images, setImages] = useState([]);
  const [imageModalOpen, setImageModalOpen] = useState(false);
  const [previewImage, setPreviewImage] = useState(null);
  const [editingImage, setEditingImage] = useState(null);

  useEffect(() => {
    let cancelled = false;
    fetch(`/releases/${experiment}/${releaseId}/images`)
      .then((response) => (response.ok ? response.json() : null))
      .then((data) => {
        if (!cancelled && data) setImages(data.images || []);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [experiment, releaseId]);

  return (
    <>
      <div>
        <div className="records-table-toolbar">
          <div className="records-table-toolbar-buttons">
            <Button
              color="blue"
              disabled={editDisabled}
              onClick={() => setAddModalOpen(true)}
            >
              <Icon name="plus" /> Add Document
            </Button>
            <Button
              color="blue"
              disabled={editDisabled || documents.length === 0}
              onClick={() => setImageModalOpen(true)}
            >
              <Icon name="image" /> Upload Images
            </Button>
          </div>
        </div>
        <Table celled compact>
          <Table.Header>
            <Table.Row>
              <Table.HeaderCell>Slug / Path</Table.HeaderCell>
              <Table.HeaderCell>Title</Table.HeaderCell>
              <Table.HeaderCell>Type</Table.HeaderCell>
              <Table.HeaderCell collapsing>Actions</Table.HeaderCell>
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {visible.length === 0 ? (
              <Table.Row>
                <Table.Cell colSpan="4" textAlign="center">
                  No documents in this release.
                </Table.Cell>
              </Table.Row>
            ) : (
              visible.flatMap((doc, i) => {
                const docImages = images.filter(
                  (img) => img.parent_slug === doc.slug,
                );
                return [
                  <Table.Row key={`doc-${doc.slug || i}`}>
                    <Table.Cell className="no-glossary">
                      {doc.slug || "—"}
                    </Table.Cell>
                    <Table.Cell>{doc.title || "—"}</Table.Cell>
                    <Table.Cell>{doc.type?.primary || "—"}</Table.Cell>
                    <Table.Cell collapsing>
                      <RowActions
                        onEdit={() => setEditingDoc(doc)}
                        editDisabled={editDisabled}
                        viewDisabled={viewDisabled}
                        viewHref={doc.slug ? `/docs/${doc.slug}` : undefined}
                      />
                    </Table.Cell>
                  </Table.Row>,
                  ...docImages.map((image) => (
                    <Table.Row
                      key={`img-${image.parent_slug}-${image.filename}`}
                    >
                      <Table.Cell className="no-glossary">
                        <span className="image-row-url">{image.url}</span>
                        <Button
                          icon
                          basic
                          size="mini"
                          className="image-row-copy-btn"
                          title="Copy path"
                          onClick={() =>
                            navigator.clipboard.writeText(image.url)
                          }
                        >
                          <Icon name="copy outline" />
                        </Button>
                      </Table.Cell>
                      <Table.Cell className="no-glossary">
                        {image.filename}
                      </Table.Cell>
                      <Table.Cell>Image</Table.Cell>
                      <Table.Cell collapsing>
                        <RowActions
                          onEdit={() => setEditingImage(image)}
                          onView={() => setPreviewImage(image)}
                          editDisabled={editDisabled}
                        />
                      </Table.Cell>
                    </Table.Row>
                  )),
                ];
              })
            )}
          </Table.Body>
        </Table>

        {documents.length > pageSize && (
          <div className="records-table-pagination">
            <Pagination
              totalPages={totalPages}
              activePage={page + 1}
              onPageChange={(_, d) => setPage(d.activePage - 1)}
            />
          </div>
        )}
      </div>

      <AddDocumentModal
        open={addModalOpen}
        onClose={() => setAddModalOpen(false)}
        experiment={experiment}
        releaseId={releaseId}
        onAdded={(newDocs) => setDocuments((prev) => [...prev, ...newDocs])}
      />

      <EditDocumentModal
        doc={editingDoc}
        onClose={() => setEditingDoc(null)}
        experiment={experiment}
        releaseId={releaseId}
        onSaved={(updated) =>
          setDocuments((prev) => {
            const idx = prev.indexOf(editingDoc);
            if (idx === -1) return prev;
            const next = [...prev];
            next[idx] = updated;
            return next;
          })
        }
      />

      <UploadImagesModal
        open={imageModalOpen}
        onClose={() => setImageModalOpen(false)}
        experiment={experiment}
        releaseId={releaseId}
        documents={documents}
        onUploaded={(newImages) => setImages((prev) => [...prev, ...newImages])}
      />

      <PreviewImageModal
        image={previewImage}
        onClose={() => setPreviewImage(null)}
      />

      <EditImageModal
        image={editingImage}
        onClose={() => setEditingImage(null)}
        experiment={experiment}
        releaseId={releaseId}
        onRenamed={(oldImage, newImage) =>
          setImages((prev) =>
            prev.map((img) =>
              img.parent_slug === oldImage.parent_slug &&
              img.filename === oldImage.filename
                ? newImage
                : img,
            ),
          )
        }
        onDeleted={(image) =>
          setImages((prev) =>
            prev.filter(
              (img) =>
                !(
                  img.parent_slug === image.parent_slug &&
                  img.filename === image.filename
                ),
            ),
          )
        }
      />
    </>
  );
}
